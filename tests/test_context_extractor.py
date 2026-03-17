import pytest
from memento.utils.context_extractor import (
    extract_context_structure,
    parse_context,
    _extract_scope,
    _extract_components,
    _extract_conditions,
    _extract_evidence,
    _extract_temporal,
    _extract_exceptions
)

def test_extract_scope():
    assert _extract_scope("partially implemented") == "partial"
    assert _extract_scope("fully tested") == "full"
    assert _extract_scope("only in dev") == "conditional"
    assert _extract_scope("random text") is None

def test_extract_components():
    components = _extract_components("the auth module and user service")
    assert "auth module" in components
    assert "user service" in components

def test_extract_conditions():
    conditions = _extract_conditions("works when connected to DB if configured")
    assert "connected to DB if configured" in conditions
    assert "configured" in conditions

def test_extract_evidence():
    evidence = _extract_evidence("verified by integration tests")
    assert "integration tests" in evidence

def test_extract_temporal():
    assert _extract_temporal("since v1.2.3") == "v1.2.3"
    assert _extract_temporal("after restart") == "restart"

def test_extract_exceptions():
    exceptions = _extract_exceptions("all except the cache")
    assert "the cache" in exceptions

def test_extract_context_structure():
    result = extract_context_structure("partially implements auth module verified by unit tests")
    assert result["text"] == "partially implements auth module verified by unit tests"
    assert result["scope"] == "partial"
    assert "auth module" in result["components"]
    assert "unit tests" in result["evidence"]

def test_parse_context():
    # test JSON
    json_result = parse_context('{"scope": "full"}')
    assert json_result["scope"] == "full"
    
    # test free text fallback
    text_result = parse_context("fully implemented")
    assert text_result["scope"] == "full"
    assert text_result["text"] == "fully implemented"

    # test None
    assert parse_context(None) == {}
