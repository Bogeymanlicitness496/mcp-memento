
## MCP CLI COMMANDS

python -m context_server 
python -m context_server --help
python -m context_server --health

## TOOLS

Lista dei 19 Tool Esposti (Extended + Advanced):

### Core Tools (9):
1. **`store_memory`** - Store a new memory with context and metadata
2. **`get_memory`** - Retrieve a specific memory by ID
3. **`search_memories`** - Search memories using natural language queries
4. **`update_memory`** - Update an existing memory
5. **`delete_memory`** - Delete a memory by ID
6. **`create_relationship`** - Create relationships between memories
7. **`get_related_memories`** - Get memories related to a specific memory
8. **`recall_memories`** - Primary tool for finding past memories (fuzzy matching)
9. **`get_recent_activity`** - Get recent memory activity

### Extended Extra Tools (3):
10. **`get_memory_statistics`** - Get statistics about stored memories
11. **`search_relationships_by_context`** - Search relationships by context
12. **`contextual_search`** - Context-aware memory search

### Advanced Tools (7):
13. **`analyze_memory_graph`** - Analyze the memory relationship graph
14. **`find_patterns`** - Find patterns in memories
15. **`suggest_relationships`** - Suggest potential relationships between memories
16. **`get_memory_clusters`** - Get clusters of related memories
17. **`get_central_memories`** - Find central/important memories in the graph
18. **`find_path_between_memories`** - Find connection paths between memories
19. **`get_memory_network`** - Get the network structure of memories

**Totale: 19 tool**

Se vuoi solo i 12 tool del profilo "extended" (senza advanced), devi impostare `CONTEXT_ENABLE_ADVANCED_TOOLS=false` nella configurazione Zed.
