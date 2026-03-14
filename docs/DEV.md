
# MCP CLI COMMANDS

python -m context_server 
python -m context_server --help
python -m context_server --health

# TOOLS

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


# CROSS COMPILATION

### Opzione 1: Usare `cross` (la più comoda per casi complessi)
Se il tuo progetto ha dipendenze C (come spesso succede), la cross-compilation manuale può diventare un incubo. Esiste **`cross`**, un wrapper che usa Docker per gestire tutto automaticamente:

```bash
# Installa cross
cargo install cross

# Compila per Windows (senza impazzire)
cross build --target x86_64-pc-windows-gnu --release
```
`cross` si occupa di tutto: toolchain, linker, librerie di sistema .

## Casi particolari da tenere d'occhio

| Scenario | Problema | Soluzione |
|----------|----------|-----------|
| **Dipendenze C** (es. `ring`, `openssl-sys`) | La compilazione incrociata fallisce perché cerca librerie C del sistema target | Usa `cross` con Docker, o installa manualmente le librerie di cross-compilation  |
| **Glibc vs musl** | Binario Linux compilato su Ubuntu potrebbe non funzionare su CentOS vecchio (versione glibc diversa) | Compila per `x86_64-unknown-linux-musl` per avere binari statici che girano **su qualsiasi Linux**  |
| **Windows MSVC vs GNU** | `x86_64-pc-windows-msvc` (Micosoft) dà eseguibili più "nativi", ma richiede Visual Studio | Per semplicità, usa `x86_64-pc-windows-gnu` (MinGW)  |
| **macOS** | Compilare per macOS da Linux è **estremamente difficile** per via delle licenze Apple | Compila nativamente su Mac o usa CI su GitHub Actions con runner macOS  |

## Opzione 2:

Considerando che stai sviluppando un MCP server in Rust e vuoi distribuirlo su più piattaforme, ti consiglio:

1. **In fase di sviluppo**: compila nativamente sul sistema che stai usando
2. **Per le release**: usa GitHub Actions con una matrice di build che compila automaticamente per Windows, Linux e macOS 
3. **Per Linux**: considera di usare il target `musl` per avere un singolo eseguibile statico che funziona su tutte le distro

Esempio di matrice GitHub Actions:
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    target: [x86_64-unknown-linux-gnu, x86_64-pc-windows-gnu, x86_64-apple-darwin]
```
