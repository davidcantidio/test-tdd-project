import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))


def test_get_health_status(monkeypatch):
    from streamlit_extension.pages.health import get_health_status
    from streamlit_extension import __version__

    # Fake database health to make the test deterministic
    def fake_health():
        return {"status": "ok"}

    monkeypatch.setattr(
        "streamlit_extension.pages.health.check_health", fake_health, raising=False
    )

    data = get_health_status()
    assert data["status"] == "OK"
    assert data["database"] == {"status": "ok"}
    assert data["version"] == __version__

