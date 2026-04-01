"""
Abstract base class for graph database backends.

This module defines the interface for SQLite backend implementation,
ensuring compatibility with the memory server.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class GraphBackend(ABC):
    """
    Abstract base class for graph database backends.

    SQLite backend implementation must implement this interface
    to ensure compatibility with the memory server.
    """

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the database backend.

        Returns:
            bool: True if connection successful, False otherwise

        Raises:
            DatabaseConnectionError: If connection cannot be established
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close the database connection and clean up resources.

        This method should be idempotent and safe to call multiple times.
        """
        pass


    @abstractmethod
    async def initialize_schema(self) -> None:
        """
        Initialize database schema including indexes and constraints.

        This should be idempotent and safe to call multiple times.

        Raises:
            SchemaError: If schema initialization fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        Check backend health and return status information.

        Returns:
            Dictionary with health check results:
                - connected: bool
                - backend_type: str
                - version: str (if available)
                - statistics: dict (optional)
        """
        pass

    @abstractmethod
    def backend_name(self) -> str:
        """
        Return the name of this backend implementation.

        Returns:
            Backend name (always "sqlite")
        """
        pass

    @abstractmethod
    def supports_fulltext_search(self) -> bool:
        """
        Check if this backend supports full-text search.

        Returns:
            True if full-text search is supported
        """
        pass

    @abstractmethod
    def supports_transactions(self) -> bool:
        """
        Check if this backend supports ACID transactions.

        Returns:
            True if transactions are supported
        """
        pass


    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        return False

