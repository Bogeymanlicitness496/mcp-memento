#!/usr/bin/env python3
"""Example usage of MCP Context Keeper."""

import asyncio
from mcp_context_keeper import ContextKeeper, MemoryType


async def main():
    """Example main function."""
    print("MCP Context Keeper - Example Usage")
    print("=" * 40)
    
    # Initialize context keeper
    keeper = ContextKeeper()
    
    # Store some memories
    print("\n1. Storing memories...")
    
    memory1 = await keeper.store_memory(
        content="User prefers dark theme in code editor",
        memory_type=MemoryType.PREFERENCE,
        title="Editor Theme Preference",
    )
    print(f"   - Stored: {memory1.title}")
    
    memory2 = await keeper.store_memory(
        content="Project uses Python 3.11 with FastAPI backend",
        memory_type=MemoryType.CONFIGURATION,
        title="Project Tech Stack",
    )
    print(f"   - Stored: {memory2.title}")
    
    memory3 = await keeper.store_memory(
        content="Use async/await for all database operations",
        memory_type=MemoryType.DECISION,
        title="Architecture Decision",
    )
    print(f"   - Stored: {memory3.title}")
    
    # Recall memories
    print("\n2. Recalling memories about theme...")
    memories = await keeper.recall_memories("theme")
    print(f"   Found {len(memories)} memories")
    
    for i, memory in enumerate(memories, 1):
        print(f"   {i}. {memory.title}: {memory.content[:50]}...")
    
    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
