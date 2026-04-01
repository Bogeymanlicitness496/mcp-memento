import pytest
from memento.utils.project_detection import detect_project_context
import os

def test_detect_project_context():
    res = detect_project_context()
    assert isinstance(res, dict)
    assert "project_path" in res
    assert "project_name" in res
