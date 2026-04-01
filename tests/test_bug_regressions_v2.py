"""
Bug regression tests v2 — fixes introduced after March 2026 testing session.

Covers:
  BUG-01  get_recent_memento_activity — timeout without explicit project arg
  BUG-02  find_path_between_mementos — hops always 1, no path detail
  BUG-03  hardcoded wrong tool names in output (get_memory, get_related_memories)
  BUG-04  get_memento include_relationships=True — relationships never rendered
  BUG-05  memento_onboarding 'distinction' topic — false '_persistent' suffix
"""

import asyncio
import inspect
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memento.advanced_tools import AdvancedRelationshipHandlers
from memento.database.engine import SQLiteBackend
from memento.database.interface import SQLiteMemoryDatabase
from memento.models import (
    Memory,
    MemoryType,
    RelationshipProperties,
    RelationshipType,
)
from memento.tools.activity_tools import handle_get_recent_memento_activity
from memento.tools.guide_tools import handle_memento_onboarding
from memento.tools.memory_tools import handle_get_memento
from memento.tools.search_tools import (
    handle_contextual_memento_search,
    handle_recall_mementos,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as fh:
        path = fh.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
async def backend(temp_db_path):
    be = SQLiteBackend(temp_db_path)
    await be.connect()
    await be.initialize_schema()
    yield be
    await be.disconnect()


@pytest.fixture
async def db(backend):
    return SQLiteMemoryDatabase(backend)


def _make_memory(
    mem_id: str,
    title: str = "Test memory",
    mem_type: MemoryType = MemoryType.GENERAL,
    importance: float = 0.5,
    tags: list | None = None,
    content: str = "Test content",
) -> Memory:
    now = datetime.now(timezone.utc)
    return Memory(
        id=mem_id,
        type=mem_type,
        title=title,
        content=content,
        tags=tags or [],
        importance=importance,
        created_at=now,
        updated_at=now,
    )


_DEFAULT_PROPS = RelationshipProperties(strength=0.8, confidence=0.8)


async def _link(
    db: SQLiteMemoryDatabase,
    from_id: str,
    to_id: str,
    rel_type: RelationshipType = RelationshipType.SOLVES,
    props: RelationshipProperties | None = None,
) -> str:
    """Thin helper so tests don't repeat the positional-arg boilerplate."""
    return await db.create_relationship(
        from_id,
        to_id,
        rel_type,
        props or _DEFAULT_PROPS,
    )


# ---------------------------------------------------------------------------
# BUG-01  get_recent_memento_activity — git detection timeout
# ---------------------------------------------------------------------------


class TestBug01RecentActivityTimeout:
    """Tool must complete without MCP-transport timeout even on slow git."""

    @pytest.mark.asyncio
    async def test_returns_result_when_git_detection_is_slow(self, db):
        """
        Simulate a git call that takes 2 s.  The handler must still finish
        within 5 s total because its internal timeout is now <= 1 s.
        """

        def slow_detect():
            time.sleep(2.0)
            return {"project_path": "/fake"}

        with patch(
            "memento.utils.project_detection.detect_project_context",
            side_effect=slow_detect,
        ):
            result = await asyncio.wait_for(
                handle_get_recent_memento_activity(db, {"days": 1}),
                timeout=5.0,
            )

        assert not result.isError
        assert "Recent Activity" in result.content[0].text

    @pytest.mark.asyncio
    async def test_internal_timeout_is_under_one_second(self):
        """
        The asyncio.wait_for timeout used for git auto-detection must be
        <= 1.0 s so it cannot block the MCP stdio transport.
        """
        import memento.tools.activity_tools as mod

        src = inspect.getsource(mod.handle_get_recent_memento_activity)
        matches = re.findall(r"wait_for\(.*?timeout\s*=\s*([\d.]+)", src, re.DOTALL)
        assert matches, "No asyncio.wait_for(timeout=...) found in handler source"
        timeout_val = float(matches[0])
        assert timeout_val <= 1.0, (
            f"Git detection timeout is {timeout_val}s — must be ≤ 1.0s "
            "to avoid MCP transport deadline"
        )

    @pytest.mark.asyncio
    async def test_explicit_project_arg_skips_detection(self, db):
        result = await handle_get_recent_memento_activity(
            db, {"days": 7, "project": "/my/project"}
        )
        assert not result.isError
        assert "Recent Activity" in result.content[0].text


# ---------------------------------------------------------------------------
# BUG-02  find_path_between_mementos — hops always 1, no path detail
# ---------------------------------------------------------------------------


class TestBug02FindPathBetweenMementos:
    """BFS must report the real hop count and include the intermediate path."""

    @pytest.mark.asyncio
    async def test_direct_path_one_hop(self, db):
        await db.store_memory(_make_memory("a", "Node A"))
        await db.store_memory(_make_memory("b", "Node B"))
        await _link(db, "a", "b")

        handlers = AdvancedRelationshipHandlers(db)
        result = await handlers.handle_find_path_between_mementos(
            {"from_memory_id": "a", "to_memory_id": "b"}
        )

        assert not result.isError
        payload = json.loads(result.content[0].text)
        assert payload["found"] is True
        assert payload["hops"] == 1
        assert "path" in payload
        assert len(payload["path"]) == 2  # start + end

    @pytest.mark.asyncio
    async def test_two_hop_path_reported_correctly(self, db):
        """
        A → B → C: path A→C must report hops=2, not hops=1.
        This was the core bug — hops was always 1 when target was reachable.
        """
        for nid, title in (("a", "Node A"), ("b", "Node B"), ("c", "Node C")):
            await db.store_memory(_make_memory(nid, title))

        await _link(db, "a", "b", RelationshipType.WORKS_WITH)
        await _link(db, "b", "c", RelationshipType.SOLVES)

        handlers = AdvancedRelationshipHandlers(db)
        result = await handlers.handle_find_path_between_mementos(
            {"from_memory_id": "a", "to_memory_id": "c", "max_depth": 5}
        )

        assert not result.isError
        payload = json.loads(result.content[0].text)
        assert payload["found"] is True
        assert payload["hops"] == 2, (
            f"Expected hops=2 for A→B→C path, got {payload['hops']}"
        )
        assert len(payload["path"]) == 3  # A, B, C

    @pytest.mark.asyncio
    async def test_path_contains_intermediate_nodes(self, db):
        """The 'path' list must include intermediate node B."""
        for nid, title in (("a", "Alpha"), ("b", "Beta"), ("c", "Gamma")):
            await db.store_memory(_make_memory(nid, title))

        await _link(db, "a", "b")
        await _link(db, "b", "c")

        handlers = AdvancedRelationshipHandlers(db)
        result = await handlers.handle_find_path_between_mementos(
            {"from_memory_id": "a", "to_memory_id": "c"}
        )

        payload = json.loads(result.content[0].text)
        path_ids = [node["id"] for node in payload["path"]]
        assert "b" in path_ids, f"Intermediate node 'b' missing from path: {path_ids}"
        assert path_ids[0] == "a"
        assert path_ids[-1] == "c"

    @pytest.mark.asyncio
    async def test_no_path_returns_found_false(self, db):
        await db.store_memory(_make_memory("a", "Isolated A"))
        await db.store_memory(_make_memory("b", "Isolated B"))
        # No relationship between them

        handlers = AdvancedRelationshipHandlers(db)
        result = await handlers.handle_find_path_between_mementos(
            {"from_memory_id": "a", "to_memory_id": "b", "max_depth": 3}
        )

        assert not result.isError
        payload = json.loads(result.content[0].text)
        assert payload["found"] is False

    @pytest.mark.asyncio
    async def test_max_depth_respected(self, db):
        """Path of 3 hops must not be found when max_depth=2."""
        for nid in ("a", "b", "c", "d"):
            await db.store_memory(_make_memory(nid, f"Node {nid.upper()}"))

        await _link(db, "a", "b")
        await _link(db, "b", "c")
        await _link(db, "c", "d")

        handlers = AdvancedRelationshipHandlers(db)
        result = await handlers.handle_find_path_between_mementos(
            {"from_memory_id": "a", "to_memory_id": "d", "max_depth": 2}
        )

        payload = json.loads(result.content[0].text)
        assert payload["found"] is False


# ---------------------------------------------------------------------------
# BUG-03  Wrong tool names hardcoded in output strings
# ---------------------------------------------------------------------------


class TestBug03WrongToolNamesInOutput:
    """Tool output must not suggest invalid tool names to LLM consumers."""

    @pytest.mark.asyncio
    async def test_recall_mementos_no_old_tool_names(self, db):
        await db.store_memory(
            _make_memory("m1", "Redis solution", content="fix timeout", tags=["redis"])
        )

        result = await handle_recall_mementos(db, {"query": "Redis"})
        text = result.content[0].text

        assert "get_memory(" not in text, (
            "recall_mementos output still references obsolete 'get_memory' tool"
        )
        assert "get_related_memories(" not in text, (
            "recall_mementos output still references obsolete 'get_related_memories' tool"
        )
        assert "get_memento(" in text
        assert "get_related_mementos(" in text

    @pytest.mark.asyncio
    async def test_recall_mementos_confidence_tip_correct_tool_name(self, db):
        await db.store_memory(_make_memory("m1", "Test", content="content"))

        result = await handle_recall_mementos(db, {"query": "Test"})
        text = result.content[0].text

        # The tip must not use the short alias "boost_confidence"
        assert "boost_confidence`" not in text, (
            "recall_mementos still suggests 'boost_confidence' "
            "(must be 'boost_memento_confidence')"
        )
        assert "boost_memento_confidence" in text

    @pytest.mark.asyncio
    async def test_contextual_search_no_old_tool_names(self, db):
        await db.store_memory(
            _make_memory("ctx", "Context root", content="root content")
        )
        await db.store_memory(
            _make_memory("rel", "Related node", content="related content redis")
        )
        await _link(db, "ctx", "rel")

        result = await handle_contextual_memento_search(
            db, {"memory_id": "ctx", "query": "redis"}
        )
        text = result.content[0].text

        assert "get_memory(" not in text, (
            "contextual_memento_search output still references obsolete 'get_memory' tool"
        )
        assert "get_memento(" in text

    @pytest.mark.asyncio
    async def test_recent_activity_no_old_tool_names(self, db):
        # Store an unresolved problem to trigger the branch that emits the tip
        await db.store_memory(
            _make_memory("p1", "Unsolved problem", mem_type=MemoryType.PROBLEM)
        )

        result = await handle_get_recent_memento_activity(
            db, {"days": 30, "project": "/fake"}
        )
        text = result.content[0].text

        assert "get_memory(" not in text, (
            "get_recent_memento_activity output still references obsolete 'get_memory' tool"
        )


# ---------------------------------------------------------------------------
# BUG-04  get_memento include_relationships=True — relationships not rendered
# ---------------------------------------------------------------------------


class TestBug04GetMementoRelationshipsRendered:
    """get_memento with include_relationships=True must render a Relationships section."""

    @pytest.mark.asyncio
    async def test_relationships_appear_in_output(self, db):
        await db.store_memory(
            _make_memory("sol", "My Solution", mem_type=MemoryType.SOLUTION)
        )
        await db.store_memory(
            _make_memory("prob", "My Problem", mem_type=MemoryType.PROBLEM)
        )
        await _link(db, "sol", "prob", RelationshipType.SOLVES)

        result = await handle_get_memento(
            db, {"memory_id": "sol", "include_relationships": True}
        )

        assert not result.isError
        text = result.content[0].text
        assert "Relationships" in text, (
            "get_memento with include_relationships=True must render a 'Relationships' section"
        )
        assert "SOLVES" in text, "Relationship type SOLVES must appear in output"
        assert "My Problem" in text, "Related memory title must appear in output"

    @pytest.mark.asyncio
    async def test_no_relationships_section_when_none_exist(self, db):
        await db.store_memory(_make_memory("lone", "Lone memory"))

        result = await handle_get_memento(
            db, {"memory_id": "lone", "include_relationships": True}
        )

        assert not result.isError
        # Must not crash; basic info must still appear
        assert "Memory: Lone memory" in result.content[0].text

    @pytest.mark.asyncio
    async def test_include_relationships_false_skips_section(self, db):
        await db.store_memory(
            _make_memory("s2", "Solution 2", mem_type=MemoryType.SOLUTION)
        )
        await db.store_memory(
            _make_memory("p2", "Problem 2", mem_type=MemoryType.PROBLEM)
        )
        await _link(db, "s2", "p2", RelationshipType.SOLVES)

        result = await handle_get_memento(
            db, {"memory_id": "s2", "include_relationships": False}
        )

        assert not result.isError
        text = result.content[0].text
        # With include_relationships=False no extra DB call should occur
        assert "Relationships" not in text

    @pytest.mark.asyncio
    async def test_multiple_relationship_types_all_rendered(self, db):
        await db.store_memory(_make_memory("hub", "Hub node"))
        await db.store_memory(_make_memory("n1", "Node 1"))
        await db.store_memory(_make_memory("n2", "Node 2"))
        await _link(db, "hub", "n1", RelationshipType.SOLVES)
        await _link(db, "hub", "n2", RelationshipType.REQUIRES)

        result = await handle_get_memento(
            db, {"memory_id": "hub", "include_relationships": True}
        )

        text = result.content[0].text
        assert "SOLVES" in text
        assert "REQUIRES" in text


# ---------------------------------------------------------------------------
# BUG-05  memento_onboarding 'distinction' topic — false '_persistent' suffix
# ---------------------------------------------------------------------------


class TestBug05OnboardingDistinctionNoPersistentSuffix:
    """The 'distinction' topic must not describe Memento tools with '_persistent' suffix."""

    @pytest.mark.asyncio
    async def test_no_persistent_suffix_in_distinction_guide(self, db):
        result = await handle_memento_onboarding(db, {"topic": "distinction"})
        assert not result.isError
        text = result.content[0].text

        assert "_persistent" not in text, (
            "The distinction guide still contains the false '_persistent' suffix. "
            "Memento tools are named store_memento / get_memento — no suffix."
        )

    @pytest.mark.asyncio
    async def test_distinction_guide_names_correct_memento_tools(self, db):
        result = await handle_memento_onboarding(db, {"topic": "distinction"})
        text = result.content[0].text

        for tool_name in ("store_memento", "get_memento", "search_mementos"):
            assert tool_name in text, (
                f"Distinction guide must mention '{tool_name}' as a Memento tool"
            )

    @pytest.mark.asyncio
    async def test_distinction_guide_still_contrasts_with_session_tools(self, db):
        """The guide must still reference the Serena session tool names."""
        result = await handle_memento_onboarding(db, {"topic": "distinction"})
        text = result.content[0].text

        for session_tool in ("store_memory", "get_memory"):
            assert session_tool in text, (
                f"Distinction guide should still reference session tool '{session_tool}'"
            )
