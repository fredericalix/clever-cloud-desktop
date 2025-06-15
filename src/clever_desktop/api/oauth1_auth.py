"""
Clever Cloud OAuth 1.0 Authentication

OAuth 1.0 implementation for Clever Cloud API authentication
with secure token storage and proper signature generation.
"""

import asyncio
import base64
import hashlib
import hmac
import logging
import secrets
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Dict, Optional, Tuple

import httpx
import keyring
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth 1.0 callback."""
    
    def do_GET(self):
        """Handle GET request for OAuth 1.0 callback."""
        try:
            # Parse the callback URL
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Extract OAuth 1.0 parameters
            oauth_token = query_params.get('oauth_token', [None])[0]
            oauth_verifier = query_params.get('oauth_verifier', [None])[0]
            
            if oauth_token and oauth_verifier:
                logger.info("OAuth 1.0 verifier received successfully")
                self.server.auth_result = {
                    'oauth_token': oauth_token, 
                    'oauth_verifier': oauth_verifier
                }
            else:
                logger.error("Missing oauth_token or oauth_verifier in callback")
                self.server.auth_result = {'error': 'missing_parameters'}
            
            # Send response to browser
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            if oauth_token and oauth_verifier:
                html = """
                <html>
                <head>
                    <title>Clever Cloud Authentication</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        .success { color: #28a745; }
                        .logo { width: 200px; margin-bottom: 30px; }
                    </style>
                </head>
                <body>
                    <h1 class="success">✅ Authentication Successful!</h1>
                    <p>You have successfully authenticated with Clever Cloud.</p>
                    <p>You can close this window and return to the application.</p>
                    <script>setTimeout(function(){window.close();}, 3000);</script>
                </body>
                </html>
                """
            else:
                html = """
                <html>
                <head>
                    <title>Authentication Error</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        .error { color: #dc3545; }
                    </style>
                </head>
                <body>
                    <h1 class="error">❌ Authentication Error</h1>
                    <p>Missing required parameters.</p>
                    <p>You can close this window and try again.</p>
                </body>
                </html>
                """
            
            self.wfile.write(html.encode())
            
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            self.server.auth_result = {'error': str(e)}
    
    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        pass


class CleverCloudOAuth1(QObject):
    """OAuth 1.0 authentication manager for Clever Cloud."""
    
    # Signals
    authentication_success = Signal(dict)  # user_info
    authentication_failed = Signal(str)    # error_message
    logout_completed = Signal()
    token_refreshed = Signal()
    
    # Clever Cloud OAuth 1.0 endpoints
    OAUTH_BASE_URL = "https://api.clever-cloud.com"
    REQUEST_TOKEN_URL = f"{OAUTH_BASE_URL}/oauth/request_token"
    AUTHORIZE_URL = f"{OAUTH_BASE_URL}/oauth/authorize"
    ACCESS_TOKEN_URL = f"{OAUTH_BASE_URL}/oauth/access_token"
    USER_INFO_URL = f"{OAUTH_BASE_URL}/v2/self"
    
    # OAuth 1.0 configuration
    CLIENT_ID = "LeWniK6lQY9Xhb9XrlFrx3nushQ5hO"
    CLIENT_SECRET = "nLCeyh3ASZFC5ZswlHhdJAj5veZ1Gj"
    REDIRECT_URI = "http://localhost:8765/callback"
    
    # Keyring service name
    KEYRING_SERVICE = "clever-desktop-manager"
    KEYRING_USERNAME = "oauth1_tokens"
    
    def __init__(self):
        """Initialize the OAuth 1.0 authentication manager."""
        super().__init__()
        self.access_token: Optional[str] = None
        self.access_token_secret: Optional[str] = None
        self.user_info: Optional[Dict] = None
        logger.info("OAuth 1.0 authentication manager initialized")
    
    def _generate_nonce(self) -> str:
        """Generate a unique nonce for OAuth 1.0."""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    def _generate_timestamp(self) -> str:
        """Generate timestamp for OAuth 1.0."""
        return str(int(time.time()))
    
    def _generate_signature(self, method: str, url: str, params: Dict[str, str], 
                          token_secret: str = "") -> str:
        """Generate OAuth 1.0 signature using HMAC-SHA1."""
        # Create parameter string
        sorted_params = sorted(params.items())
        param_string = "&".join([f"{k}={urllib.parse.quote(str(v), safe='')}" 
                                for k, v in sorted_params])
        
        # Create signature base string
        base_string = f"{method.upper()}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(param_string, safe='')}"
        
        # Create signing key
        signing_key = f"{urllib.parse.quote(self.CLIENT_SECRET, safe='')}&{urllib.parse.quote(token_secret, safe='')}"
        
        # Generate signature
        signature = hmac.new(
            signing_key.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    def _create_auth_header(self, params: Dict[str, str]) -> str:
        """Create OAuth 1.0 authorization header."""
        oauth_params = {k: v for k, v in params.items() if k.startswith('oauth_')}
        param_string = ", ".join([f'{k}="{urllib.parse.quote(str(v), safe="")}"' 
                                 for k, v in sorted(oauth_params.items())])
        return f"OAuth {param_string}"
    
    async def _get_request_token(self) -> Tuple[str, str]:
        """Get OAuth 1.0 request token."""
        params = {
            'oauth_callback': self.REDIRECT_URI,
            'oauth_consumer_key': self.CLIENT_ID,
            'oauth_nonce': self._generate_nonce(),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': self._generate_timestamp(),
            'oauth_version': '1.0'
        }
        
        # Generate signature
        params['oauth_signature'] = self._generate_signature('POST', self.REQUEST_TOKEN_URL, params)
        
        # Create authorization header
        auth_header = self._create_auth_header(params)
        
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.REQUEST_TOKEN_URL, headers=headers)
            
            if response.status_code == 200:
                # Parse response
                response_params = urllib.parse.parse_qs(response.text)
                oauth_token = response_params['oauth_token'][0]
                oauth_token_secret = response_params['oauth_token_secret'][0]
                return oauth_token, oauth_token_secret
            else:
                logger.error(f"Request token failed: {response.status_code} - {response.text}")
                raise Exception(f"Request token failed: {response.status_code}")
    
    async def authenticate(self) -> bool:
        """Perform OAuth 1.0 authentication flow."""
        try:
            logger.info("Starting OAuth 1.0 authentication flow")
            
            # Step 1: Get request token
            request_token, request_token_secret = await self._get_request_token()
            logger.info("Request token obtained")
            
            # Step 2: Build authorization URL
            auth_url = f"{self.AUTHORIZE_URL}?oauth_token={request_token}"
            logger.info(f"Opening browser for authorization: {auth_url}")
            
            # Open browser for authorization
            webbrowser.open(auth_url)
            
            logger.info("Authentication successful")
            return True
            
        except Exception as e:
            error_msg = f"Authentication error: {e}"
            logger.error(error_msg)
            self.authentication_failed.emit(error_msg)
            return False
    
    def _store_tokens(self, access_token: str, access_token_secret: str) -> None:
        """Store access tokens securely using keyring."""
        try:
            token_data = f"{access_token}:{access_token_secret}"
            keyring.set_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME, token_data)
            logger.info("Tokens stored securely")
        except Exception as e:
            logger.error(f"Failed to store tokens: {e}")
    
    def _load_tokens(self) -> Optional[Tuple[str, str]]:
        """Load access tokens from secure storage."""
        try:
            token_data = keyring.get_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME)
            if token_data and ':' in token_data:
                access_token, access_token_secret = token_data.split(':', 1)
                logger.info("Tokens loaded from secure storage")
                return access_token, access_token_secret
            return None
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
            return None
    
    def clear_stored_auth(self) -> None:
        """Clear stored authentication data."""
        try:
            keyring.delete_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME)
            logger.info("Stored authentication cleared")
        except Exception as e:
            logger.error(f"Failed to clear stored auth: {e}")
        
        self.access_token = None
        self.access_token_secret = None
        self.user_info = None
    
    async def logout(self) -> None:
        """Logout and clear stored authentication."""
        self.clear_stored_auth()
        self.logout_completed.emit()
        logger.info("User logged out")
    
    async def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        if not self.access_token or not self.access_token_secret:
            # Try to load from storage
            stored_tokens = self._load_tokens()
            if stored_tokens:
                self.access_token, self.access_token_secret = stored_tokens
                try:
                    # Verify tokens by getting user info
                    self.user_info = await self._get_user_info(self.access_token, self.access_token_secret)
                    return True
                except Exception:
                    # Tokens are invalid, clear them
                    self.clear_stored_auth()
                    return False
        
        if self.access_token and self.access_token_secret:
            try:
                # Verify tokens are still valid
                await self._get_user_info(self.access_token, self.access_token_secret)
                return True
            except Exception:
                # Tokens are invalid, clear them
                self.clear_stored_auth()
                return False
        
        return False
    
    def get_access_token(self) -> Optional[str]:
        """Get the current access token."""
        return self.access_token
    
    def get_access_token_secret(self) -> Optional[str]:
        """Get the current access token secret."""
        return self.access_token_secret
    
    def get_user_info(self) -> Optional[Dict]:
        """Get the current user information."""
        return self.user_info
    
    def get_auth_headers(self, method: str, url: str, params: Optional[Dict] = None) -> Dict[str, str]:
        """Get OAuth 1.0 signed headers for API requests."""
        if not self.access_token or not self.access_token_secret:
            return {}
        
        oauth_params = {
            'oauth_consumer_key': self.CLIENT_ID,
            'oauth_nonce': self._generate_nonce(),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': self._generate_timestamp(),
            'oauth_token': self.access_token,
            'oauth_version': '1.0'
        }
        
        # Add any additional parameters for signature
        all_params = oauth_params.copy()
        if params:
            all_params.update(params)
        
        # Generate signature
        oauth_params['oauth_signature'] = self._generate_signature(
            method, url, all_params, self.access_token_secret
        )
        
        # Create authorization header
        auth_header = self._create_auth_header(oauth_params)
        
        return {
            'Authorization': auth_header,
            'Accept': 'application/json'
        }

    async def _get_user_info(self, access_token: str, access_token_secret: str) -> Dict:
        """Get user information using OAuth 1.0 signed request."""
        params = {
            'oauth_consumer_key': self.CLIENT_ID,
            'oauth_nonce': self._generate_nonce(),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': self._generate_timestamp(),
            'oauth_token': access_token,
            'oauth_version': '1.0'
        }
        
        # Generate signature with access token secret
        params['oauth_signature'] = self._generate_signature(
            'GET', self.USER_INFO_URL, params, access_token_secret
        )
        
        # Create authorization header
        auth_header = self._create_auth_header(params)
        
        headers = {
            'Authorization': auth_header,
            'Accept': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.USER_INFO_URL, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"User info request failed: {response.status_code} - {response.text}")
                raise Exception(f"User info request failed: {response.status_code}") 