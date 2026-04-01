import pytest
from memento.utils.pagination import paginate_memories, count_memories
from unittest.mock import AsyncMock, MagicMock
from memento.models import SearchQuery

@pytest.mark.asyncio
async def test_paginate_memories():
    db = MagicMock()
    async def mock_search(query):
        if query.offset == 0:
            return ["item1", "item2"]
        elif query.offset == 2:
            return ["item3"]
        return []
    
    db.search_memories = mock_search
    del db.search_memories_paginated
    
    batches = []
    async for batch in paginate_memories(db, batch_size=2):
        batches.append(batch)
        
    assert len(batches) == 2
    assert batches[0] == ["item1", "item2"]
    assert batches[1] == ["item3"]

@pytest.mark.asyncio
async def test_count_memories():
    db = MagicMock()
    async def mock_search(query):
        if query.offset == 0:
            return ["item1", "item2", "item3"]
        return []
    
    db.search_memories = mock_search
    del db.search_memories_paginated
    
    count = await count_memories(db)
    assert count == 3
