import os
from typing import Optional
import asyncpg
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Database connection pool
_connection_pool: Optional[asyncpg.Pool] = None


async def get_database() -> asyncpg.Pool:
    """
    Get database connection pool

    Returns:
        Database connection pool
    """
    global _connection_pool

    if _connection_pool is None:
        database_url = os.getenv("DATABASE_URL", "postgresql://root:mysecretpassword@localhost:5432/local")

        try:
            _connection_pool = await asyncpg.create_pool(
                database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise

    return _connection_pool


async def close_database():
    """Close database connection pool"""
    global _connection_pool

    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None
        logger.info("Database connection pool closed")