"""
Clever Cloud API Token Authentication

Simple API token authentication for Clever Cloud API
with secure token storage.
"""

import asyncio
import logging
import webbrowser
from typing import Dict, Optional

import httpx
import keyring
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class CleverCloudTokenAuth(QObject):
    """Clever Cloud API Token authentication manager."""
    
    # Signals
    authentication_success = Signal(dict)  # user_info
    authentication_failed = Signal(str)    # error_message
    logout_completed = Signal()
    token_refreshed = Signal()
    token_input_required = Signal()  # request token input from user
    
    # Clever Cloud API endpoints
    API_BASE_URL = "https://api-bridge.clever-cloud.com"
    
    # Keyring configuration
    KEYRING_SERVICE = "clever-desktop"
    KEYRING_USERNAME = "api-token"
    
    def __init__(self):
        super().__init__()
        self.api_token = None
        self.user_info = None
        logger.info("API Token authentication manager initialized")
    
    def get_api_token(self) -> Optional[str]:
        """Get current API token."""
        return self.api_token
    
    def get_auth_headers(self, method: str = None, url: str = None, params: dict = None) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        if not self.api_token:
            return {}
        
        return {
            "Authorization": f"Bearer {self.api_token}"
        }
    
    async def authenticate(self) -> None:
        """Start API token authentication flow."""
        logger.info("Starting API token authentication flow")
        
        try:
            # Check for stored token first
            if await self.load_stored_token():
                logger.info("Using stored API token")
                return
            
            # If no stored token, guide user to create one
            await self._guide_token_creation()
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            self.authentication_failed.emit(f"Authentication error: {e}")
    
    async def load_stored_token(self) -> bool:
        """Load stored API token."""
        try:
            stored_token = keyring.get_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME)
            if stored_token:
                self.api_token = stored_token
                
                # Verify token by making a test request
                if await self._verify_token():
                    logger.info("Stored API token is valid")
                    return True
                else:
                    logger.warning("Stored API token is invalid, clearing it")
                    self.clear_stored_auth()
                    
        except Exception as e:
            logger.error(f"Failed to load stored token: {e}")
        
        return False
    
    async def _verify_token(self) -> bool:
        """Verify API token by making a test request."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.API_BASE_URL}/v2/self",
                    headers=self.get_auth_headers(),
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.user_info = response.json()
                    self.authentication_success.emit(self.user_info)
                    return True
                else:
                    logger.error(f"Token verification failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False
    
    async def _guide_token_creation(self) -> None:
        """Guide user to create an API token."""
        logger.info("Guiding user to create API token")
        
        # Emit signal to request token input from main thread
        self.token_input_required.emit()
    
    def store_token(self, token: str) -> None:
        """Store API token securely."""
        try:
            keyring.set_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME, token)
            self.api_token = token
            logger.info("API token stored successfully")
            
            # Verify the token asynchronously using a task
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule the verification
                    task = asyncio.create_task(self._verify_token())
                    # We can't wait for it here since we're in the same loop
                    # The verification will emit signals when complete
                else:
                    # If no loop is running, create one
                    result = asyncio.run(self._verify_token())
                    if not result:
                        self.authentication_failed.emit("Token verification failed")
            except RuntimeError:
                # Fallback: try to run in new loop
                try:
                    result = asyncio.run(self._verify_token())
                    if not result:
                        self.authentication_failed.emit("Token verification failed")
                except Exception as e:
                    logger.error(f"Token verification failed: {e}")
                    self.authentication_failed.emit("Token verification failed")
            
        except Exception as e:
            logger.error(f"Failed to store token: {e}")
            self.authentication_failed.emit(f"Failed to store token: {e}")
    
    def clear_stored_auth(self) -> None:
        """Clear stored authentication data."""
        try:
            keyring.delete_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME)
            logger.info("Stored authentication cleared")
        except Exception as e:
            logger.error(f"Failed to clear stored auth: {e}")
        
        self.api_token = None
        self.user_info = None
    
    async def logout(self) -> None:
        """Logout and clear stored authentication."""
        self.clear_stored_auth()
        self.logout_completed.emit()
        logger.info("User logged out")
    
    async def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return self.api_token is not None and await self._verify_token()
    
    async def close(self) -> None:
        """Close authentication manager and cleanup resources."""
        # No specific cleanup needed for token auth
        logger.info("Token authentication manager closed") 