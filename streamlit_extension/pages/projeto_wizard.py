#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧙‍♂️ Projeto Wizard Page Wrapper

This is a wrapper file that imports and renders the actual projeto wizard
from the projeto_wizard subdirectory, as Streamlit requires page files 
to be directly in the pages/ directory.
"""

from __future__ import annotations

# Import the actual wizard implementation
import sys
import os

# Add the parent directory to path to enable absolute imports  
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Now import using absolute path and expose a thin wrapper
from streamlit_extension.pages.projetos.projeto_wizard import (
    render_projeto_wizard_page as _render_projeto_wizard_page_impl,
)

def render_projeto_wizard_page(*args, **kwargs):
    """Re-exported entry that simply delegates to the implementation.

    Important: Do not auto-render on import. The app orchestrator calls this
    function explicitly, and auto-rendering would cause duplicate rendering
    and Streamlit key collisions.
    """
    return _render_projeto_wizard_page_impl(*args, **kwargs)

# If executed directly as a standalone Streamlit page script
if __name__ == "__main__":
    render_projeto_wizard_page()
