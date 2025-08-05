"""
Authentication module for BorgDash
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from config import Config


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class AuthManager:
    """Authentication manager"""
    
    def __init__(self, config: Config):
        self.config = config
        # Cache for job configs and their API keys
        self._job_api_keys = None
        self._api_key_to_job_mapping = None
    
    def _load_job_api_keys(self) -> set:
        """Load all API keys from job configuration files"""
        if self._job_api_keys is not None:
            return self._job_api_keys
            
        from config import get_all_job_configs
        
        api_keys = set()
        api_key_to_job_mapping = {}
        
        # Add API tokens from main config (these have access to all jobs)
        for token in self.config.auth.api_tokens:
            api_keys.add(token)
            api_key_to_job_mapping[token] = "*"  # Wildcard for all jobs
        
        # Add API keys from job configs (these are job-specific)
        job_configs = get_all_job_configs(self.config.server.config_dir)
        for job_id, job_config in job_configs.items():
            if 'api_keys' in job_config:
                for api_key in job_config['api_keys']:
                    api_keys.add(api_key)
                    api_key_to_job_mapping[api_key] = job_id
        
        self._job_api_keys = api_keys
        self._api_key_to_job_mapping = api_key_to_job_mapping
        return api_keys
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """Verify username and password"""
        return (username == self.config.auth.username and 
                password == self.config.auth.password)
    
    def create_access_token(self, username: str) -> tuple[str, datetime]:
        """Create JWT access token"""
        expires_at = datetime.utcnow() + timedelta(hours=self.config.auth.jwt_expire_hours)
        
        payload = {
            "sub": username,
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        token = jwt.encode(payload, self.config.auth.jwt_secret, algorithm="HS256")
        return token, expires_at
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return username if valid"""
        try:
            payload = jwt.decode(token, self.config.auth.jwt_secret, algorithms=["HS256"])
            username = payload.get("sub")
            if username is None:
                return None
            return username
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def verify_api_token(self, token: str) -> bool:
        """Verify API token for push endpoints"""
        valid_tokens = self._load_job_api_keys()
        return token in valid_tokens
    
    def verify_api_token_for_job(self, token: str, job_id: str) -> bool:
        """Verify API token has permission for specific job_id"""
        # First check if token is valid at all
        if not self.verify_api_token(token):
            return False
        
        # Load the mapping if not already loaded
        if self._api_key_to_job_mapping is None:
            self._load_job_api_keys()
        
        # Check if token has access to this job
        if self._api_key_to_job_mapping is not None:
            allowed_job = self._api_key_to_job_mapping.get(token)
            return allowed_job == "*" or allowed_job == job_id
        
        return False
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> str:
        """Dependency to get current authenticated user"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        username = self.verify_token(credentials.credentials)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return username
