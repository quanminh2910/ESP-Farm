"""
Authentication service for user login and session management.
Handles user credentials against the Supabase users table.
"""

from typing import Optional, Dict, Any
import hashlib
import threading
from config.settings import Settings
from models.supabase_models import UserInfo
from services.supabase_service import SupabaseClientSingleton
from utils.logger import get_logger

logger = get_logger(__name__)

# Thread-local storage for current user session
_user_context = threading.local()


class AuthService:
    """Service for user authentication and session management"""
    
    def __init__(self):
        """Initialize auth service with Supabase client singleton"""
        self._supabase = SupabaseClientSingleton()
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Hash a password using SHA-256
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def signup(
        self,
        username: str,
        password: str,
        email: Optional[str] = None
    ) -> UserInfo:
        """
        Register a new user
        
        Args:
            username: Username (must be unique)
            password: Plain text password
            email: Optional email address
        
        Returns:
            UserInfo of the created user
            
        Raises:
            ValueError: If username already exists
            Exception: If signup fails
        """
        try:
            # Check if username already exists
            existing = self._supabase.select(
                "users",
                filters={"username": username}
            )
            if existing:
                raise ValueError(f"Username '{username}' already exists")
            
            hashed_pwd = self._hash_password(password)
            user_data: UserInfo = {
                "username": username,
                "password": hashed_pwd,
                "email": email or None,
            }
            
            result = self._supabase.insert("users", user_data)
            logger.info(f"[AUTH] User signup successful: username={username}")
            return result
        except Exception as e:
            logger.error(f"[AUTH] Signup failed for {username}: {str(e)}")
            raise
    
    def login(self, username: str, password: str) -> UserInfo:
        """
        Authenticate a user and establish session
        
        Args:
            username: Username
            password: Plain text password
        
        Returns:
            UserInfo of the authenticated user
            
        Raises:
            ValueError: If authentication fails
            Exception: If login fails
        """
        try:
            # Query user by username
            users = self._supabase.select(
                "users",
                filters={"username": username}
            )
            if not users:
                raise ValueError(f"User '{username}' not found")
            
            user = users[0]
            hashed_pwd = self._hash_password(password)
            
            if user.get("password") != hashed_pwd:
                raise ValueError("Invalid password")
            
            # Set current user in thread-local storage
            _user_context.current_user = user
            logger.info(f"[AUTH] User login successful: username={username}")
            return user
        except Exception as e:
            logger.error(f"[AUTH] Login failed for {username}: {str(e)}")
            raise
    
    def logout(self) -> None:
        """Clear the current user session"""
        try:
            if hasattr(_user_context, 'current_user'):
                username = _user_context.current_user.get("username", "unknown")
                delattr(_user_context, 'current_user')
                logger.info(f"[AUTH] User logout successful: username={username}")
        except Exception as e:
            logger.error(f"[AUTH] Logout failed: {str(e)}")
    
    @staticmethod
    def get_current_user() -> Optional[UserInfo]:
        """
        Get the currently logged-in user
        
        Returns:
            UserInfo of current user, or None if not logged in
        """
        return getattr(_user_context, 'current_user', None)
    
    @staticmethod
    def get_current_user_id() -> int:
        """
        Get the ID of the currently logged-in user
        
        Returns:
            User ID, or SYSTEM_USER_ID if not logged in
        """
        user = AuthService.get_current_user()
        if user and user.get("user_id"):
            return user["user_id"]
        # Return system user ID for automation
        return Settings.SYSTEM_USER_ID
    
    def get_user_by_id(self, user_id: int) -> Optional[UserInfo]:
        """
        Retrieve user info by user ID
        
        Args:
            user_id: User ID
        
        Returns:
            UserInfo or None if not found
        """
        try:
            users = self._supabase.select(
                "users",
                filters={"user_id": user_id}
            )
            return users[0] if users else None
        except Exception as e:
            logger.error(f"[AUTH] Failed to get user by ID {user_id}: {str(e)}")
            raise
