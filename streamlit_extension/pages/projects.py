#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 Projects Page Wrapper

This is a wrapper file that imports and renders the actual projects page
from the projetos subdirectory, as Streamlit requires page files 
to be directly in the pages/ directory.
"""

from __future__ import annotations

# Import the actual projects implementation
import sys
import os

# Add the parent directory to path to enable absolute imports  
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Now import using absolute path
from streamlit_extension.pages.projetos.projects import render_projects_page

# This file serves as a Streamlit page entry point
if __name__ == "__main__":
    render_projects_page()
else:
    # When imported as a module, render the page
    render_projects_page()