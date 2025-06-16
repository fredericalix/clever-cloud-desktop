"""
Clever Cloud API Client

HTTP client for interacting with Clever Cloud APIs.
Handles authentication, requests, caching, and response parsing.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urljoin

import httpx

from .token_auth import CleverCloudTokenAuth
from ..models.config import AuthConfig, ApiConfig


class ApiError(Exception):
    """API request error."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class CleverCloudClient:
    """Clever Cloud API client with OAuth2 authentication."""
    
    # API Base URLs
    API_V2_BASE = "https://api-bridge.clever-cloud.com/v2"
    API_V4_BASE = "https://api-bridge.clever-cloud.com/v4"
    
    def __init__(self, settings=None, cache_dir: Optional[Path] = None):
        self.settings = settings
        self.cache_dir = cache_dir or Path.cwd() / "cache"
        self.logger = logging.getLogger(__name__)
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.auth_config = AuthConfig() if not settings else AuthConfig()
        self.api_config = ApiConfig() if not settings else ApiConfig()
        
        # HTTP client with retries
        self.client = httpx.AsyncClient(
            timeout=self.api_config.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        # Authentication manager
        self.auth = CleverCloudTokenAuth()
        
        # Cache for API responses
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("Clever Cloud API client initialized")
    
    # Authentication methods
    def has_stored_credentials(self) -> bool:
        """Check if stored credentials are available."""
        try:
            import keyring
            stored_data = keyring.get_password(self.auth.KEYRING_SERVICE, self.auth.KEYRING_USERNAME)
            return stored_data is not None
        except Exception:
            return False
    
    async def authenticate_with_stored_credentials(self) -> bool:
        """Authenticate using stored credentials."""
        try:
            return await self.auth.is_authenticated()
        except Exception as e:
            self.logger.error(f"Failed to authenticate with stored credentials: {e}")
            return False
    
    async def start_authentication(self) -> None:
        """Start OAuth 1.0 authentication flow."""
        await self.auth.authenticate()
    
    def is_session_valid(self) -> bool:
        """Check if current session is valid."""
        return self.auth.get_api_token() is not None
    
    async def refresh_session(self) -> bool:
        """OAuth 1.0 tokens don't need refresh."""
        return await self.auth.is_authenticated()
    
    async def logout(self) -> None:
        """Logout and clear credentials."""
        self.auth.clear_stored_auth()
        self._cache.clear()
    
    # API Request methods
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        api_version: str = "v2",
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        use_cache: bool = True,
        cache_duration: int = 300
    ) -> Dict[str, Any]:
        """Make authenticated API request with caching and retry logic."""
        
        # Build URL
        base_url = self.API_V2_BASE if api_version == "v2" else self.API_V4_BASE
        # Ensure proper URL joining - add trailing slash to base and remove leading slash from endpoint
        if not base_url.endswith('/'):
            base_url += '/'
        endpoint = endpoint.lstrip('/')
        url = urljoin(base_url, endpoint)
        
        # Check cache first
        cache_key = f"{method}:{url}:{json.dumps(params or {}, sort_keys=True)}"
        if use_cache and method.upper() == "GET":
            cached_response = self._get_cached_response(cache_key, cache_duration)
            if cached_response:
                self.logger.debug(f"Cache hit for {url}")
                return cached_response
        
        # Prepare headers
        headers = {}
        if self.auth.get_api_token():
            headers.update(self.auth.get_auth_headers())
        
        # Retry logic
        for attempt in range(self.api_config.retry_count + 1):
            try:
                start_time = datetime.now()
                
                # Make request
                response = await self.client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                )
                
                duration = (datetime.now() - start_time).total_seconds()
                self.logger.debug(f"API {method.upper()} {url} -> {response.status_code} ({duration:.3f}s)")
                
                # Handle response
                if response.status_code == 401:
                    # OAuth 1.0 tokens don't refresh, just fail
                    raise ApiError("Authentication failed", 401)
                
                response.raise_for_status()
                response_data = response.json()
                
                # Cache successful GET requests
                if use_cache and method.upper() == "GET":
                    self._cache_response(cache_key, response_data)
                
                return response_data
                
            except httpx.HTTPStatusError as e:
                if attempt == self.api_config.retry_count:
                    error_data = None
                    try:
                        error_data = e.response.json()
                    except:
                        pass
                    
                    raise ApiError(
                        f"HTTP {e.response.status_code}: {e.response.text}",
                        e.response.status_code,
                        error_data
                    )
                
                self.logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                if attempt == self.api_config.retry_count:
                    raise ApiError(f"Request failed: {str(e)}")
                
                self.logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(2 ** attempt)
    
    def _get_cached_response(self, cache_key: str, cache_duration: int) -> Optional[Dict]:
        """Get cached response if still valid."""
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data["timestamp"])
            if datetime.now() - cache_time < timedelta(seconds=cache_duration):
                return cached_data["data"]
        return None
    
    def _cache_response(self, cache_key: str, data: Dict) -> None:
        """Cache API response."""
        self._cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Simple cache cleanup - remove old entries
        if len(self._cache) > 1000:
            oldest_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k]["timestamp"]
            )[:100]
            for key in oldest_keys:
                del self._cache[key]
    
    # User and Organization API
    async def get_user_info(self) -> Dict[str, Any]:
        """Get current user information."""
        return await self._make_request("GET", "/self")
    
    async def get_organizations(self) -> List[Dict[str, Any]]:
        """Get user's organizations."""
        response = await self._make_request("GET", "/organisations")
        return response if isinstance(response, list) else []
    
    async def get_organization(self, org_id: str) -> Dict[str, Any]:
        """Get organization details."""
        return await self._make_request("GET", f"/organisations/{org_id}")
    
    # Applications API  
    async def get_applications(self, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get applications for organization."""
        if org_id:
            endpoint = f"/organisations/{org_id}/applications"
        else:
            endpoint = "/self/applications"
        
        response = await self._make_request("GET", endpoint)
        return response if isinstance(response, list) else []
    
    async def get_application(self, app_id: str) -> Dict[str, Any]:
        """Get application details."""
        return await self._make_request("GET", f"/applications/{app_id}")
    
    async def create_application(
        self, 
        org_id: str, 
        name: str, 
        app_type: str, 
        region: str = "par",
        **kwargs
    ) -> Dict[str, Any]:
        """Create new application."""
        data = {
            "name": name,
            "deploy": app_type,
            "zone": region,
            **kwargs
        }
        return await self._make_request("POST", f"/organisations/{org_id}/applications", data=data)
    
    async def delete_application(self, app_id: str) -> bool:
        """Delete application."""
        try:
            await self._make_request("DELETE", f"/applications/{app_id}")
            return True
        except ApiError:
            return False
    
    async def start_application(self, app_id: str) -> Dict[str, Any]:
        """Start application."""
        return await self._make_request("POST", f"/applications/{app_id}/instances")
    
    async def stop_application(self, app_id: str) -> Dict[str, Any]:
        """Stop application."""
        return await self._make_request("DELETE", f"/applications/{app_id}/instances")
    
    async def restart_application(self, app_id: str) -> Dict[str, Any]:
        """Restart application."""
        return await self._make_request("POST", f"/applications/{app_id}/instances/restart")
    
    async def get_application_instances(self, app_id: str) -> List[Dict[str, Any]]:
        """Get application instances."""
        response = await self._make_request("GET", f"/applications/{app_id}/instances")
        return response if isinstance(response, list) else []
    
    async def get_application_env(self, app_id: str, org_id: Optional[str] = None) -> Dict[str, Any]:
        """Get application environment variables."""
        if org_id:
            endpoint = f"/organisations/{org_id}/applications/{app_id}/env"
        else:
            endpoint = f"/applications/{app_id}/env"
        return await self._make_request("GET", endpoint)
    
    async def set_application_env(self, app_id: str, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Set application environment variables."""
        return await self._make_request("PUT", f"/applications/{app_id}/env", data=env_vars)
    
    # Add-ons API
    async def get_addons(self, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get add-ons for organization."""
        if org_id:
            endpoint = f"/organisations/{org_id}/addons"
        else:
            endpoint = "/self/addons"
        
        response = await self._make_request("GET", endpoint)
        return response if isinstance(response, list) else []
    
    async def get_addon(self, addon_id: str) -> Dict[str, Any]:
        """Get add-on details."""
        return await self._make_request("GET", f"/addons/{addon_id}")
    
    async def create_addon(
        self,
        org_id: str,
        provider_id: str,
        name: str,
        plan: str,
        region: str = "par",
        **kwargs
    ) -> Dict[str, Any]:
        """Create new add-on."""
        data = {
            "name": name,
            "providerId": provider_id,
            "plan": plan,
            "region": region,
            **kwargs
        }
        return await self._make_request("POST", f"/organisations/{org_id}/addons", data=data)
    
    # Network Groups API (v4)
    async def get_network_groups(self, org_id: str) -> List[Dict[str, Any]]:
        """Get Network Groups for organization."""
        # Use the same endpoint format as the CLI
        response = await self._make_request("GET", f"/networkgroups/organisations/{org_id}/networkgroups", api_version="v4")
        return response if isinstance(response, list) else []
    
    async def get_network_group(self, ng_id: str) -> Dict[str, Any]:
        """Get Network Group details."""
        return await self._make_request("GET", f"/networkgroups/{ng_id}", api_version="v4")
    
    async def create_network_group(self, org_id: str, name: str, **kwargs) -> Dict[str, Any]:
        """Create new Network Group."""
        data = {
            "organisationId": org_id,
            "name": name,
            **kwargs
        }
        return await self._make_request("POST", "/networkgroups", api_version="v4", data=data)
    
    async def get_network_group_members(self, ng_id: str) -> List[Dict[str, Any]]:
        """Get Network Group members."""
        # Use the correct endpoint format for members
        response = await self._make_request("GET", f"/networkgroups/{ng_id}/members", api_version="v4")
        return response if isinstance(response, list) else []
    
    async def create_external_peer(
        self,
        ng_id: str,
        peer_label: str,
        wireguard_public_key: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create external peer in Network Group."""
        data = {
            "peerLabel": peer_label,
            "wireguardPublicKey": wireguard_public_key,
            **kwargs
        }
        return await self._make_request("POST", f"/networkgroups/{ng_id}/external-peers", api_version="v4", data=data)
    
    # Logs API
    async def get_application_logs(
        self,
        app_id: str,
        limit: int = 100,
        since: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get application logs."""
        params = {"limit": limit}
        if since:
            params["since"] = since
        
        response = await self._make_request("GET", f"/applications/{app_id}/logs", params=params)
        return response if isinstance(response, list) else []
    
    # Deployment API
    async def trigger_deployment(self, app_id: str, git_ref: str = "master") -> Dict[str, Any]:
        """Trigger application deployment."""
        data = {"gitRef": git_ref}
        return await self._make_request("POST", f"/applications/{app_id}/deployments", data=data)
    
    async def get_deployments(self, app_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get application deployments."""
        params = {"limit": limit}
        response = await self._make_request("GET", f"/applications/{app_id}/deployments", params=params)
        return response if isinstance(response, list) else []
    
    # Utility methods
    async def close(self) -> None:
        """Close client and cleanup resources."""
        await self.auth.close()
        await self.client.aclose()
        self.logger.info("API client closed")
    
    def clear_cache(self) -> None:
        """Clear API response cache."""
        self._cache.clear()
        self.logger.info("API cache cleared") 