# MCP Context Keeper v0.1.15

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol-blueviolet)](https://spec.modelcontextprotocol.io/)

**Intelligent persistent memory management for MCP clients** with automatic confidence tracking, relationship mapping, and knowledge quality maintenance.

**Version:** v0.1.15 | **Latest:** Confidence system reorganization with tools now available in Core profile

## 🚀 Quick Start

### Installation
```bash
# Install with pipx (recommended)
pipx install mcp-context-keeper

# Or with pip
pip install mcp-context-keeper
```

### Basic Configuration
Add to your MCP client configuration (e.g., Zed Editor, Cursor, Windsurf):

```json
{
  "mcpServers": {
    "context_keeper": {
      "command": "context_keeper",
      "args": ["--profile", "extended"],
      "env": {
        "CONTEXT_SQLITE_PATH": "~/.mcp-context-keeper/context.db"
      }
    }
  }
}
```

### First Memory
```python
# Store a solution
store_persistent_memory(
    type="solution",
    title="Fixed Redis timeout with connection pooling",
    content="Increased connection timeout to 30s and added connection pooling...",
    tags=["redis", "timeout", "production_fix"],
    importance=0.8
)

# Find it later
recall_persistent_memories(query="Redis timeout solutions")
```

## ✨ Key Features

### 🧠 **Intelligent Confidence System**
- **Automatic decay**: Unused knowledge loses confidence over time (5% monthly)
- **Critical protection**: Security/auth/API key memories never decay
- **Boost on validation**: Confidence increases when knowledge is successfully used
- **Smart ordering**: Search results ranked by `confidence × importance`

### 🔗 **Relationship Mapping**
- **35+ relationship types**: SOLVES, CAUSES, IMPROVES, USED_IN, etc.
- **Graph navigation**: Find connections between concepts
- **Pattern detection**: Identify recurring solution patterns
- **Knowledge clusters**: Discover topic groups and related concepts

### 📊 **Three Profile System**
| Profile | Tools | Best For |
|---------|-------|----------|
| **Core** | 13 tools | All users - Essential operations + confidence basics |
| **Extended** | 17 tools | Power users - Analytics + contextual search |
| **Advanced** | 25 tools | Administrators - Graph analysis + advanced configuration |

### 🗃️ **Persistent Storage**
- **SQLite backend**: Zero dependencies, local storage
- **Full-text search**: Fast, fuzzy matching across all memories
- **Automatic maintenance**: Confidence decay, relationship integrity
- **Export/import**: JSON export for backup and migration

## 📚 Documentation

### Essential Guides
- **[Tools Reference](docs/TOOLS.md)** - Complete guide to all 25 MCP tools
- **[Confidence System](docs/DECAY_SYSTEM.md)** - How confidence tracking works
- **[Database Schema](docs/SCHEMA.md)** - Technical database structure
- **[Usage Rules](docs/RULES.md)** - Best practices and templates

### Tool Profiles

#### **Core Profile (13 tools) - Recommended for Everyone**
```python
# Essential memory operations
store_persistent_memory()        # Store new knowledge
get_persistent_memory()          # Retrieve by ID
search_persistent_memories()     # Advanced search
recall_persistent_memories()     # Natural language search (RECOMMENDED)

# Relationships
create_persistent_relationship() # Connect memories
get_related_persistent_memories() # Explore connections

# Confidence management (NEW in Core!)
get_persistent_low_confidence_memories() # Find obsolete knowledge
boost_persistent_confidence()    # Reinforce valid knowledge
adjust_persistent_confidence()   # Manual correction
```

#### **Extended Profile (17 tools) - Power Users**
All Core tools plus:
- `get_persistent_memory_statistics()` - Database metrics
- `persistent_contextual_search()` - Scoped search
- `apply_persistent_confidence_decay()` - Automatic maintenance

#### **Advanced Profile (25 tools) - Administrators**
All Extended tools plus:
- Graph analysis tools (7 tools)
- Pattern detection
- Cluster analysis
- `set_persistent_decay_factor()` - Advanced confidence configuration

## 🎯 Usage Examples

### Store and Connect Knowledge
```python
# Store a problem
problem_id = store_persistent_memory(
    type="problem",
    title="API rate limiting causing timeouts",
    content="External API returns 429 errors during peak loads...",
    tags=["api", "rate-limiting", "production"],
    importance=0.7
)

# Store the solution
solution_id = store_persistent_memory(
    type="solution",
    title="Implemented exponential backoff for API calls",
    content="Added jitter and circuit breaker pattern...",
    tags=["api", "resilience", "python"],
    importance=0.8
)

# Connect them
create_persistent_relationship(
    from_memory_id=solution_id,
    to_memory_id=problem_id,
    relationship_type="SOLVES"
)
```

### Find Obsolete Knowledge
```python
# Monthly maintenance
low_conf = get_persistent_low_confidence_memories(threshold=0.3)

for memory in low_conf:
    if validate_memory(memory):
        # Still valid - boost confidence
        boost_persistent_confidence(
            memory_id=memory.id,
            boost_amount=0.2,
            reason="Monthly verification"
        )
    else:
        # Obsolete - mark for review
        adjust_persistent_confidence(
            relationship_id=memory.relationship_id,
            new_confidence=0.1,
            reason="Obsolete after library update"
        )
```

### Natural Language Search
```python
# Find authentication patterns
results = recall_persistent_memories(
    query="JWT authentication middleware patterns",
    memory_types=["solution", "pattern"],
    limit=10
)

# Results automatically sorted by confidence
for memory in results:
    print(f"{memory.title} (confidence: {memory.confidence:.2f})")
```

## ⚙️ Configuration

### Environment Variables
```bash
# Database path
export CONTEXT_SQLITE_PATH="~/.mcp-context-keeper/context.db"

# Tool profile (core|extended|advanced)
export CONTEXT_TOOL_PROFILE="extended"

# Logging
export CONTEXT_LOG_LEVEL="INFO"
```

### YAML Configuration
Create `context-keeper.yaml` in your project:
```yaml
backend: "sqlite"
sqlite_path: "~/.mcp-context-keeper/context.db"
tool_profile: "extended"
enable_advanced_tools: false
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
features:
  allow_relationship_cycles: false
```

### CLI Usage
```bash
# Run server with specific profile
context_keeper --profile extended

# Health check
context_keeper --health

# Show configuration
context_keeper --show-config

# Export memories
context_keeper --export memories.json

# Import memories
context_keeper --import memories.json
```

## 🏗️ Architecture

### Database Schema
```sql
-- Core tables
memories (id, type, title, content, tags, importance, created_at, updated_at)
relationships (id, from_memory_id, to_memory_id, type, confidence, last_accessed)

-- Full-text search
memories_fts (title, content, tags)  -- Virtual table for fast search

-- Confidence tracking
confidence FLOAT DEFAULT 0.8
last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
access_count INTEGER DEFAULT 0
decay_factor FLOAT DEFAULT 0.95  -- 5% monthly decay
```

### Confidence System
- **Base decay**: 5% per month for unused knowledge
- **No decay**: Security/auth/API key/critical tags
- **Reduced decay**: High importance memories
- **Automatic boost**: +0.01 per access, +0.05-0.20 for validation

## 🔄 Integration Examples

### Zed Editor
```json
{
  "mcpServers": {
    "context_keeper": {
      "command": "context_keeper",
      "args": ["--profile", "extended"],
      "env": {
        "CONTEXT_SQLITE_PATH": "~/.mcp-context-keeper/context.db"
      }
    }
  }
}
```

### Cursor / Windsurf
```json
{
  "mcpServers": {
    "context-keeper": {
      "command": "context_keeper",
      "args": ["--profile", "core"]
    }
  }
}
```

### Custom Script
```python
import asyncio
from context_keeper.server import ContextKeeper

async def main():
    keeper = ContextKeeper()
    # Use keeper.tools to access available tools
    print(f"Available tools: {len(keeper.tools)}")

asyncio.run(main())
```

## 📈 Best Practices

### Memory Creation
1. **Store solutions, not just problems**
2. **Use descriptive titles** - "Fixed Redis timeout" not "Bug fix"
3. **Tag consistently** - Use existing tags when possible
4. **Set appropriate importance** - 0.9+ for critical, 0.7-0.8 for important
5. **Create relationships** - Connect related memories immediately

### Confidence Management
1. **Monthly review** - Check `get_persistent_low_confidence_memories()`
2. **Boost validated knowledge** - Use `boost_persistent_confidence()` after successful application
3. **Protect critical info** - Use `security`, `auth`, `api_key`, `critical` tags for no-decay
4. **Adjust when needed** - Use `adjust_persistent_confidence()` for corrections

### Search Optimization
1. **Start with `recall_persistent_memories()`** - Best for natural language
2. **Use `search_persistent_memories()`** for exact matches
3. **Filter by memory types** - `memory_types=["solution", "pattern"]`
4. **Explore relationships** - Use `get_related_persistent_memories()` after finding a memory

## 🚨 Troubleshooting

### Common Issues

**"Command not found" after installation**
```bash
# Ensure pipx is in PATH
pipx ensurepath
# Restart terminal
```

**Database permission errors**
```bash
# Check file permissions
ls -la ~/.mcp-context-keeper/

# Fix permissions
chmod 755 ~/.mcp-context-keeper
chmod 644 ~/.mcp-context-keeper/context.db
```

**Memory not found in search**
```python
# Try different search methods
recall_persistent_memories(query="your query")  # Fuzzy matching
search_persistent_memories(query="your query", search_tolerance="strict")  # Exact
```

### Debug Mode
```bash
# Enable debug logging
export CONTEXT_LOG_LEVEL="DEBUG"
context_keeper --profile core

# Check server status
context_keeper --health
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_confidence_system.py -v
pytest tests/test_tools.py -v

# Run with coverage
pytest --cov=context_keeper tests/
```

## 📦 Development

### Setup
```bash
# Clone repository
git clone https://github.com/yourusername/mcp-context-keeper.git
cd mcp-context-keeper

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run demo
python examples/confidence_system_demo.py
```

### Project Structure
```
mcp-context-keeper/
├── context_keeper/
│   ├── __init__.py          # Package exports and version
│   ├── server.py            # MCP server implementation
│   ├── config.py            # Configuration management
│   ├── models.py            # Data models (Memory, Relationship)
│   ├── database/
│   │   ├── engine.py        # SQLite connection management
│   │   └── interface.py     # Database operations interface
│   └── tools/
│       ├── definitions.py   # MCP tool definitions
│       ├── registry.py      # Tool handler registry
│       ├── memory_tools.py  # Memory CRUD handlers
│       ├── confidence_tools.py  # Confidence system handlers
│       └── guide_tools.py   # Help and guidance tools
├── docs/
│   ├── TOOLS.md             # Complete tool reference
│   ├── DECAY_SYSTEM.md      # Confidence system documentation
│   ├── SCHEMA.md            # Database schema
│   └── RULES.md             # Usage rules and templates
├── examples/
│   └── confidence_system_demo.py  # Demonstration script
├── tests/
│   ├── test_confidence_system.py  # Confidence system tests
│   ├── test_tools.py        # Tool handler tests
│   └── utils/               # Test utilities
├── pyproject.toml           # Project configuration
└── README.md               # This file
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Development Guidelines
- Follow existing code style
- Add comprehensive tests
- Update documentation
- Use Conventional Commits for commit messages
- Keep the confidence system backward compatible

## 🔗 Links

- **[Full Tool Reference](docs/TOOLS.md)** - Complete guide to all 25 MCP tools
- **[Confidence System](docs/DECAY_SYSTEM.md)** - How confidence tracking works
- **[Database Schema](docs/SCHEMA.md)** - Technical database structure
- **[Issue Tracker](https://github.com/yourusername/mcp-context-keeper/issues)** - Report bugs or request features
- **[MCP Specification](https://spec.modelcontextprotocol.io/)** - Model Context Protocol documentation

---

**MCP Context Keeper** transforms your coding assistant from a passive tool into an **intelligent knowledge partner** that learns from your work, maintains accuracy over time, and helps you build on past successes.