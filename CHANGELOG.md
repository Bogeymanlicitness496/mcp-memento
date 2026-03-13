# Changelog

All notable changes to the mcp-user-memory project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial changelog file

## [0.1.4] - 2026-03-13

### Added
- SQLite-only backend support (removed all other backends)
- Simplified configuration with YAML + env vars
- MemoryNode.to_database_properties() method for SQLite compatibility
- Updated documentation reflecting SQLite-only architecture

### Changed
- Simplified project structure by removing non-SQLite backends
- Updated README.md to reflect SQLite-only support
- Removed references to Neo4j, FalkorDB, Memgraph, Turso, and Cloud backends
- Updated memory_parser.py documentation

### Fixed
- Critical bug preventing memory storage in SQLite backend
- Documentation inconsistencies
- Import/export functionality for SQLite

### Removed
- Multi-tenant support
- All non-SQLite backend implementations
- Admin-only tools and migration tools
- Advanced analytics modules not essential for core functionality

## [0.1.3] - 2026-03-12

### Added
- Initial simplified version for Zed editor integration
- Core MCP tools for memory management
- SQLite backend with zero dependencies
- Basic configuration system

### Changed
- Project renamed to mcp-user-memory
- Focus on single-user, local storage use case
- Simplified architecture for Zed editor compatibility

## [0.1.2] - 2026-03-11

### Added
- Export/import functionality for memories
- Health check CLI command
- Basic relationship management

### Fixed
- SQLite schema initialization issues
- Memory parsing utilities

## [0.1.1] - 2026-03-10

### Added
- Initial SQLite backend implementation
- Core memory models (Memory, MemoryContext, Relationship)
- Basic tool handlers for MCP protocol

### Changed
- Ported from original MemoryGraph project
- Simplified for single-backend operation

## [0.1.0] - 2026-03-09

### Added
- Initial project setup
- MCP server foundation
- Basic project structure

---

## Versioning Scheme

- **Major version (0.x.y)**: Breaking changes to API or architecture
- **Minor version (0.x.y)**: New features and enhancements
- **Patch version (0.x.y.z)**: Bug fixes and minor improvements

## Migration Notes

### From v0.1.3 to v0.1.4
- This version removes all non-SQLite backend support
- Configuration is now simplified with only SQLite options
- Multi-tenant features have been removed
- The system is now focused on single-user, local storage for Zed editor

### From original MemoryGraph
- This fork focuses on simplicity and Zed editor integration
- Only SQLite backend is supported
- Advanced features have been removed in favor of core functionality
- The project is now named "mcp-user-memory" to reflect its purpose

## Acknowledgments

This project is a simplified fork of the original MemoryGraph project by Gregory Dickson, adapted specifically for Zed editor integration with a focus on simplicity and local storage.