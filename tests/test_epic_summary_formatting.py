import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from streamlit_extension.streamlit_app import format_epic_summary


def test_format_epic_summary_handles_none():
    epic = {"summary": None, "description": None}
    assert format_epic_summary(epic) == "No description available"


def test_format_epic_summary_truncates_long_text():
    text = "a" * 150
    epic = {"summary": text}
    result = format_epic_summary(epic)
    assert result.startswith("a" * 100)
    assert result.endswith("...")
    assert len(result) == 103