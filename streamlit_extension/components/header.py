"""
📋 Header Component - Dynamic Greeting and Title

Pure UI function for rendering application header with time-based greetings.
Optimized for compatibility and clarity.
"""

import streamlit as st
from datetime import datetime
from typing import Optional

def _greeting(now: datetime) -> str:
    h = now.hour
    return "Bom dia" if h < 12 else ("Boa tarde" if h < 18 else "Boa noite")

def render_header(now: Optional[datetime] = None) -> None:
    now = now or datetime.now()
    greeting = _greeting(now)

    st.markdown(
        f"""
# 🚀 TDD Framework
## {greeting}! Bem-vindo ao sistema de desenvolvimento orientado a testes
### Gerencie seus projetos com metodologia TDD
"""
    )