"""
Supabase client singleton for database operations.
Handles connection initialization, retry logic, and query execution.
"""

from typing import Any, Dict, List, Optional
from supabase import create_client, Client
from config.settings import Settings
from utils.logger import get_logger

logger = get_logger(__name__)


class SupabaseClientSingleton:
    """Singleton for Supabase client connection"""
    _instance: Optional["SupabaseClientSingleton"] = None
    
    def __new__(cls) -> "SupabaseClientSingleton":
        if cls._instance is None:
            cls._instance = super(SupabaseClientSingleton, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize the Supabase client connection"""
        try:
            if not Settings.SUPABASE_URL or not Settings.SUPABASE_KEY:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_KEY must be set in environment variables"
                )
            
            self._client: Client = create_client(
                Settings.SUPABASE_URL,
                Settings.SUPABASE_KEY
            )
            logger.info("[SUPABASE] Successfully initialized Supabase client")
        except Exception as e:
            logger.error(f"[SUPABASE] Failed to initialize client: {str(e)}")
            raise
    
    def get_client(self) -> Client:
        """Get the Supabase client instance"""
        return self._client
    
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a row into a table
        
        Args:
            table: Table name
            data: Dictionary of column-value pairs
        
        Returns:
            Inserted row data
            
        Raises:
            Exception: If insert fails
        """
        try:
            response = self._client.table(table).insert(data).execute()
            logger.info(f"[SUPABASE] Inserted into {table}: {data}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"[SUPABASE] Insert failed for {table}: {str(e)}")
            raise
    
    def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Select rows from a table
        
        Args:
            table: Table name
            columns: Columns to select (default: all)
            filters: Dictionary of column-value pairs for filtering
        
        Returns:
            List of rows
            
        Raises:
            Exception: If select fails
        """
        try:
            query = self._client.table(table).select(columns)
            
            if filters:
                for column, value in filters.items():
                    query = query.eq(column, value)
            
            response = query.execute()
            logger.info(f"[SUPABASE] Selected from {table}: {len(response.data)} rows")
            return response.data
        except Exception as e:
            logger.error(f"[SUPABASE] Select failed for {table}: {str(e)}")
            raise
    
    def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update rows in a table
        
        Args:
            table: Table name
            data: Dictionary of column-value pairs to update
            filters: Dictionary of column-value pairs for filtering rows to update
        
        Returns:
            Updated row data
            
        Raises:
            Exception: If update fails
        """
        try:
            query = self._client.table(table).update(data)
            
            for column, value in filters.items():
                query = query.eq(column, value)
            
            response = query.execute()
            logger.info(f"[SUPABASE] Updated {table} with filters {filters}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"[SUPABASE] Update failed for {table}: {str(e)}")
            raise
    
    def delete(
        self,
        table: str,
        filters: Dict[str, Any]
    ) -> None:
        """
        Delete rows from a table
        
        Args:
            table: Table name
            filters: Dictionary of column-value pairs for filtering rows to delete
            
        Raises:
            Exception: If delete fails
        """
        try:
            query = self._client.table(table).delete()
            
            for column, value in filters.items():
                query = query.eq(column, value)
            
            response = query.execute()
            logger.info(f"[SUPABASE] Deleted from {table} with filters {filters}")
        except Exception as e:
            logger.error(f"[SUPABASE] Delete failed for {table}: {str(e)}")
            raise
