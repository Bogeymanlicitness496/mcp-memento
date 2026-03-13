"""
MemoryGraph MCP Server for Zed Editor

A graph-based MCP server that provides intelligent memory capabilities for Zed editor,
enabling persistent knowledge tracking, relationship mapping, and contextual development assistance.

Supports SQLite backend only for simplified deployment with Zed editor.
"""

__version__ = "0.1.4"
__author__ = "Gregory Dickson"
__email__ = "gregory.d.dickson@gmail.com"

from .models import (
    BackendError,
    ConfigurationError,
    DatabaseConnectionError,
    Memory,
    MemoryContext,
    MemoryError,
    MemoryNode,
    MemoryNotFoundError,
    MemoryType,
    NotFoundError,
    Relationship,
    RelationshipError,
    RelationshipType,
    SchemaError,
    ValidationError,
)
from .server import MemoryGraphServer

__all__ = [
    "MemoryGraphServer",
    "Memory",
    "MemoryType",
    "Relationship",
    "RelationshipType",
    "MemoryNode",
    "MemoryContext",
    "MemoryError",
    "MemoryNotFoundError",
    "RelationshipError",
    "ValidationError",
    "DatabaseConnectionError",
    "SchemaError",
    "NotFoundError",
    "BackendError",
    "ConfigurationError",
]
