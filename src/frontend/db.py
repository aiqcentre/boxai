"""
Database connection module supporting DuckDB and PostgreSQL.
"""
import os
from typing import Any, Optional
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class DatabaseType(Enum):
    """Supported database types."""
    DUCKDB = "duckdb"
    POSTGRES = "postgres"


class DatabaseConnection:
    """
    Database connection wrapper supporting multiple database types.
    
    Configuration via environment variables:
    - DB_TYPE: "duckdb" or "postgres" (default: "duckdb")
    - DB_PATH: Path to DuckDB file (for DuckDB)
    - POSTGRES_HOST: PostgreSQL host (for PostgreSQL)
    - POSTGRES_PORT: PostgreSQL port (default: 5432)
    - POSTGRES_DB: PostgreSQL database name
    - POSTGRES_USER: PostgreSQL username
    - POSTGRES_PASSWORD: PostgreSQL password
    """
    
    def __init__(self):
        self.db_type = self._get_db_type()
        self.conn = None
        self._connect()
    
    def _get_db_type(self) -> DatabaseType:
        """Determine database type from environment variables."""
        db_type_str = os.getenv("DB_TYPE", "duckdb").lower()
        try:
            return DatabaseType(db_type_str)
        except ValueError:
            raise ValueError(
                f"Invalid DB_TYPE: {db_type_str}. Must be 'duckdb' or 'postgres'"
            )
    
    def _connect(self):
        """Establish database connection based on type."""
        if self.db_type == DatabaseType.DUCKDB:
            self._connect_duckdb()
        elif self.db_type == DatabaseType.POSTGRES:
            self._connect_postgres()
    
    def _connect_duckdb(self):
        """Connect to DuckDB database."""
        import duckdb
        
        db_path = os.getenv("DB_PATH", "src/data/numero.duckdb")
        self.conn = duckdb.connect(db_path, read_only=True)
        print(f"✓ Connected to DuckDB: {db_path}")
    
    def _connect_postgres(self):
        """Connect to PostgreSQL database."""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError:
            raise ImportError(
                "psycopg2 is required for PostgreSQL support. "
                "Install it with: pip install psycopg2-binary"
            )
        
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB")
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        
        if not all([database, user, password]):
            raise ValueError(
                "Missing required PostgreSQL credentials. "
                "Set POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD environment variables."
            )
        
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            cursor_factory=RealDictCursor,
            # Add keepalive settings to prevent timeout
            connect_timeout=30,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5
        )
        print(f"✓ Connected to PostgreSQL: {host}:{port}/{database}")
    
    def is_closed(self) -> bool:
        """Check if the database connection is closed."""
        if self.conn is None:
            return True
        
        if self.db_type == DatabaseType.POSTGRES:
            return self.conn.closed != 0
        elif self.db_type == DatabaseType.DUCKDB:
            # DuckDB doesn't have a closed property, assume open if conn exists
            return False
        
        return True
    
    def reconnect(self):
        """Reconnect to the database if connection is closed."""
        if self.is_closed():
            print(f"⚠️  Connection closed. Reconnecting to {self.db_type.value}...")
            self._connect()
    
    def execute(self, query: str) -> Any:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query string
            
        Returns:
            Query results with a fetchdf() method for pandas DataFrame
        """
        # Check and reconnect if necessary
        if self.is_closed():
            self.reconnect()
        
        if self.db_type == DatabaseType.DUCKDB:
            return self.conn.execute(query)
        elif self.db_type == DatabaseType.POSTGRES:
            return PostgresResultWrapper(self.conn, query)
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print(f"✓ Closed {self.db_type.value} connection")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class PostgresResultWrapper:
    """
    Wrapper for PostgreSQL results to provide DuckDB-like interface.
    Provides a fetchdf() method to return results as pandas DataFrame.
    """
    
    def __init__(self, conn, query: str):
        self.conn = conn
        self.query = query
    
    def fetchdf(self):
        """Execute query and return results as pandas DataFrame."""
        import pandas as pd
        
        with self.conn.cursor() as cursor:
            cursor.execute(self.query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Convert RealDictRow to regular dict
            data = [dict(row) for row in rows]
            
            return pd.DataFrame(data, columns=columns)


def get_connection() -> DatabaseConnection:
    """
    Get a database connection based on environment configuration.
    
    Returns:
        DatabaseConnection instance
    """
    return DatabaseConnection()


# Convenience function for getting database type
def get_db_type() -> str:
    """Get the configured database type."""
    return os.getenv("DB_TYPE", "duckdb").lower()
