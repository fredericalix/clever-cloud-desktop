"""
Clever Cloud OAuth2 Authentication

Complete OAuth2 implementation for Clever Cloud authentication
with secure token storage and automatic refresh.
"""

import json
import logging
import secrets
import webbrowser
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

import httpx
import keyring
from PySide6.QtCore import QObject, Signal, QTimer, QUrl
from PySide6.QtGui import QDesktopServices

from ..models.config import AuthConfig


class OAuth2Error(Exception):
    """OAuth2 authentication error."""
    pass


class CleverCloudAuth(QObject):
    """Clever Cloud OAuth2 authentication manager."""
    
    # Signals
    authentication_success = Signal(dict)  # user_info
    authentication_failed = Signal(str)    # error_message
    token_refreshed = Signal()
    logout_completed = Signal()
    
    # Clever Cloud OAuth2 endpoints
    OAUTH_BASE_URL = "https://api.clever-cloud.com/v2"
    AUTHORIZE_URL = f"{OAUTH_BASE_URL}/oauth/authorize"
    TOKEN_URL = f"{OAUTH_BASE_URL}/oauth/access_token"
    USER_INFO_URL = f"{OAUTH_BASE_URL}/self"
    
    # Application OAuth2 credentials (registered with Clever Cloud)
    CLIENT_ID = "LeWniK6lQY9Xhb9XrlFrx3nushQ5hO"
    CLIENT_SECRET = "nLCeyh3ASZFC5ZswlHhdJAj5veZ1Gj"
    REDIRECT_URI = "http://localhost:8765/callback"
    
    KEYRING_SERVICE = "clever-desktop"
    KEYRING_USERNAME = "oauth_tokens"
    
    def __init__(self, config: AuthConfig):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Token state
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.user_info: Optional[Dict[str, Any]] = None
        
        # HTTP client
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._check_token_refresh)
        self.refresh_timer.start(60000)  # Check every minute
        
        self.logger.info("OAuth2 authentication manager initialized")
    
    async def start_authentication(self) -> None:
        """Start the OAuth2 authentication flow."""
        try:
            self.logger.info("Starting OAuth2 authentication flow")
            
            # Generate state parameter for security
            state = secrets.token_urlsafe(32)
            
            # Build authorization URL
            params = {
                "response_type": "code",
                "client_id": self.CLIENT_ID,
                "redirect_uri": self.REDIRECT_URI,
                "scope": "read write",  # Adjust scopes as needed
                "state": state,
            }
            
            auth_url = f"{self.AUTHORIZE_URL}?" + urllib.parse.urlencode(params)
            
            self.logger.info(f"Opening browser for authorization: {auth_url}")
            
            # Open browser for user authorization
            QDesktopServices.openUrl(QUrl(auth_url))
            
            # Start local server to receive callback
            await self._start_callback_server(state)
            
        except Exception as e:
            self.logger.error(f"Failed to start authentication: {e}")
            self.authentication_failed.emit(str(e))
    
    async def _start_callback_server(self, expected_state: str) -> None:
        """Start local server to receive OAuth2 callback."""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        import queue
        
        result_queue = queue.Queue()
        
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse callback URL
                parsed_url = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed_url.query)
                
                if "code" in params and "state" in params:
                    code = params["code"][0]
                    state = params["state"][0]
                    
                    # Send success response
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"""
                    <html><body>
                    <h1>Authentication Successful!</h1>
                    <p>You can close this window and return to Clever Desktop.</p>
                    <script>setTimeout(function(){window.close();}, 3000);</script>
                    </body></html>
                    """)
                    
                    result_queue.put(("success", code, state))
                elif "error" in params:
                    error = params["error"][0]
                    error_description = params.get("error_description", [""])[0]
                    
                    # Send error response
                    self.send_response(400)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(f"""
                    <html><body>
                    <h1>Authentication Failed</h1>
                    <p>Error: {error}</p>
                    <p>Description: {error_description}</p>
                    </body></html>
                    """.encode())
                    
                    result_queue.put(("error", error, error_description))
                
            def log_message(self, format, *args):
                # Suppress HTTP server logs
                pass
        
        # Start server
        server = HTTPServer(("localhost", 8765), CallbackHandler)
        server.timeout = 120  # 2 minutes timeout
        
        def run_server():
            server.handle_request()
        
        server_thread = threading.Thread(target=run_server)
        server_thread.start()
        
        # Wait for result
        try:
            result = result_queue.get(timeout=120)
            server_thread.join(timeout=1)
            
            if result[0] == "success":
                code, state = result[1], result[2]
                
                if state != expected_state:
                    raise OAuth2Error("State parameter mismatch - possible CSRF attack")
                
                await self._exchange_code_for_token(code)
            else:
                error, description = result[1], result[2]
                raise OAuth2Error(f"Authentication failed: {error} - {description}")
                
        except queue.Empty:
            raise OAuth2Error("Authentication timeout - no callback received")
        finally:
            server.server_close()
    
    async def _exchange_code_for_token(self, code: str) -> None:
        """Exchange authorization code for access token."""
        try:
            self.logger.info("Exchanging authorization code for access token")
            
            data = {
                "grant_type": "authorization_code",
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "code": code,
                "redirect_uri": self.REDIRECT_URI,
            }
            
            response = await self.client.post(self.TOKEN_URL, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Extract tokens
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)
            
            # Calculate expiration time
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # Store tokens securely
            await self._store_tokens()
            
            # Get user info
            await self._fetch_user_info()
            
            self.logger.info("Authentication successful")
            self.authentication_success.emit(self.user_info)
            
        except Exception as e:
            self.logger.error(f"Failed to exchange code for token: {e}")
            self.authentication_failed.emit(str(e))
    
    async def _fetch_user_info(self) -> None:
        """Fetch user information from API."""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = await self.client.get(self.USER_INFO_URL, headers=headers)
            response.raise_for_status()
            
            self.user_info = response.json()
            self.logger.info(f"User info fetched: {self.user_info.get('name', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Failed to fetch user info: {e}")
            self.user_info = {"name": "Unknown User", "email": "unknown@example.com"}
    
    async def _store_tokens(self) -> None:
        """Store tokens securely using keyring."""
        try:
            token_data = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
                "user_info": self.user_info,
            }
            
            keyring.set_password(
                self.KEYRING_SERVICE,
                self.KEYRING_USERNAME,
                json.dumps(token_data)
            )
            
            self.logger.info("Tokens stored securely")
            
        except Exception as e:
            self.logger.error(f"Failed to store tokens: {e}")
    
    async def load_stored_tokens(self) -> bool:
        """Load tokens from secure storage."""
        try:
            stored_data = keyring.get_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME)
            
            if not stored_data:
                return False
            
            token_data = json.loads(stored_data)
            
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            self.user_info = token_data.get("user_info")
            
            if token_data.get("expires_at"):
                self.token_expires_at = datetime.fromisoformat(token_data["expires_at"])
            
            # Check if token is still valid
            if self.token_expires_at and datetime.now() >= self.token_expires_at:
                self.logger.info("Stored token expired, attempting refresh")
                return await self.refresh_access_token()
            
            # Verify token by fetching user info
            await self._fetch_user_info()
            
            self.logger.info("Stored tokens loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load stored tokens: {e}")
            return False
    
    async def refresh_access_token(self) -> bool:
        """Refresh access token using refresh token."""
        if not self.refresh_token:
            self.logger.error("No refresh token available")
            return False
        
        try:
            self.logger.info("Refreshing access token")
            
            data = {
                "grant_type": "refresh_token",
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "refresh_token": self.refresh_token,
            }
            
            response = await self.client.post(self.TOKEN_URL, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Update tokens
            self.access_token = token_data["access_token"]
            if "refresh_token" in token_data:
                self.refresh_token = token_data["refresh_token"]
            
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # Store updated tokens
            await self._store_tokens()
            
            self.logger.info("Access token refreshed successfully")
            self.token_refreshed.emit()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to refresh access token: {e}")
            return False
    
    def _check_token_refresh(self) -> None:
        """Check if token needs refreshing."""
        if not self.token_expires_at or not self.config.auto_refresh:
            return
        
        time_until_expiry = (self.token_expires_at - datetime.now()).total_seconds()
        
        if time_until_expiry <= self.config.token_refresh_threshold:
            self.logger.info("Token nearing expiry, scheduling refresh")
            # Use async refresh in a thread to avoid blocking Qt
            import asyncio
            import threading
            
            def refresh_thread():
                asyncio.run(self.refresh_access_token())
            
            threading.Thread(target=refresh_thread, daemon=True).start()
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return (
            self.access_token is not None and
            self.token_expires_at is not None and
            datetime.now() < self.token_expires_at
        )
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        if not self.access_token:
            raise OAuth2Error("No access token available")
        
        return {"Authorization": f"Bearer {self.access_token}"}
    
    async def logout(self) -> None:
        """Logout user and clear all stored tokens."""
        try:
            self.logger.info("Logging out user")
            
            # Clear in-memory tokens
            self.access_token = None
            self.refresh_token = None
            self.token_expires_at = None
            self.user_info = None
            
            # Clear stored tokens
            try:
                keyring.delete_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME)
            except keyring.errors.PasswordDeleteError:
                pass  # Token wasn't stored
            
            self.logout_completed.emit()
            
        except Exception as e:
            self.logger.error(f"Error during logout: {e}")
    
    async def close(self) -> None:
        """Close authentication manager and cleanup resources."""
        self.refresh_timer.stop()
        await self.client.aclose()
        self.logger.info("Authentication manager closed") 