"""Minimal health check page for Streamlit app.

Provides a lightweight endpoint that can be used as a liveness signal.
It reports the application status, database connectivity and current
package version.  The implementation intentionally avoids heavy
dependencies – it only performs a simple database health check using the
existing helper and surfaces the results on a Streamlit page.
"""

from __future__ import annotations

from typing import Dict

from streamlit_extension import __version__
from streamlit_extension.database import check_health


def get_health_status() -> Dict[str, object]:
    """Return minimal health status information.

    Returns
    -------
    Dict[str, object]
        Dictionary containing service status, database health details and
        the current package version.
    """

    return {
        "status": "OK",
        "database": check_health(),
        "version": __version__,
    }


def render_health_page() -> None:  # pragma: no cover - requires streamlit
    """Render Streamlit page exposing basic health information."""

    import streamlit as st

    st.success("OK")
    st.json(get_health_status())


__all__ = ["get_health_status", "render_health_page"]

