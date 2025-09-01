"""
Summary utilities for Product Vision.

This module provides utilities for rendering the Product Vision summary
in various formats.
"""

from typing import Dict, Any, List
import streamlit as st


def render_compact_summary(pv_data: Dict[str, Any]):
    """
    Render a compact summary of the Product Vision.
    
    Args:
        pv_data: Dictionary with Product Vision data
    """
    if not pv_data:
        st.info("Nenhum dado de Product Vision disponível")
        return
        
    # Vision Statement
    vision = pv_data.get("vision_statement", "")
    if vision:
        st.markdown(f"**🎯 Visão:** {_truncate(vision, 100)}")
    
    # Problem Statement
    problem = pv_data.get("problem_statement", "")
    if problem:
        st.markdown(f"**❗ Problema:** {_truncate(problem, 100)}")
    
    # Target Audience
    audience = pv_data.get("target_audience", "")
    if audience:
        st.markdown(f"**👥 Público:** {_truncate(audience, 50)}")
    
    # Value Proposition
    value = pv_data.get("value_proposition", "")
    if value:
        st.markdown(f"**💎 Valor:** {_truncate(value, 100)}")
    
    # Constraints
    constraints = pv_data.get("constraints", [])
    if constraints:
        st.markdown("**🚧 Restrições:**")
        for i, constraint in enumerate(constraints[:3]):  # Show first 3
            st.markdown(f"  • {constraint}")
        if len(constraints) > 3:
            st.markdown(f"  _...e mais {len(constraints) - 3} restrições_")


def render_detailed_summary(pv_data: Dict[str, Any]):
    """
    Render a detailed summary of the Product Vision.
    
    Args:
        pv_data: Dictionary with Product Vision data
    """
    if not pv_data:
        st.info("Nenhum dado de Product Vision disponível")
        return
    
    st.markdown("### 📋 Product Vision Completo")
    
    # Vision Statement
    with st.expander("🎯 Declaração de Visão", expanded=True):
        vision = pv_data.get("vision_statement", "_Não definido_")
        st.write(vision)
        _render_field_metrics("vision_statement", vision)
    
    # Problem Statement
    with st.expander("❗ Problema a Resolver", expanded=True):
        problem = pv_data.get("problem_statement", "_Não definido_")
        st.write(problem)
        _render_field_metrics("problem_statement", problem)
    
    # Target Audience
    with st.expander("👥 Público-alvo", expanded=True):
        audience = pv_data.get("target_audience", "_Não definido_")
        st.write(audience)
        _render_field_metrics("target_audience", audience)
    
    # Value Proposition
    with st.expander("💎 Proposta de Valor", expanded=True):
        value = pv_data.get("value_proposition", "_Não definido_")
        st.write(value)
        _render_field_metrics("value_proposition", value)
    
    # Constraints
    with st.expander("🚧 Restrições", expanded=True):
        constraints = pv_data.get("constraints", [])
        if constraints:
            for constraint in constraints:
                st.markdown(f"• {constraint}")
        else:
            st.write("_Nenhuma restrição definida_")
        _render_field_metrics("constraints", constraints)


def export_as_markdown(pv_data: Dict[str, Any]) -> str:
    """
    Export Product Vision as markdown text.
    
    Args:
        pv_data: Dictionary with Product Vision data
        
    Returns:
        Markdown formatted string
    """
    md_lines = ["# Product Vision\n"]
    
    # Vision Statement
    vision = pv_data.get("vision_statement", "")
    if vision:
        md_lines.append(f"## 🎯 Declaração de Visão\n{vision}\n")
    
    # Problem Statement
    problem = pv_data.get("problem_statement", "")
    if problem:
        md_lines.append(f"## ❗ Problema a Resolver\n{problem}\n")
    
    # Target Audience
    audience = pv_data.get("target_audience", "")
    if audience:
        md_lines.append(f"## 👥 Público-alvo\n{audience}\n")
    
    # Value Proposition
    value = pv_data.get("value_proposition", "")
    if value:
        md_lines.append(f"## 💎 Proposta de Valor\n{value}\n")
    
    # Constraints
    constraints = pv_data.get("constraints", [])
    if constraints:
        md_lines.append("## 🚧 Restrições")
        for constraint in constraints:
            md_lines.append(f"- {constraint}")
        md_lines.append("")
    
    return "\n".join(md_lines)


def get_completion_percentage(pv_data: Dict[str, Any]) -> int:
    """
    Calculate the completion percentage of the Product Vision.
    
    Args:
        pv_data: Dictionary with Product Vision data
        
    Returns:
        Percentage (0-100)
    """
    if not pv_data:
        return 0
    
    fields = [
        "vision_statement",
        "problem_statement",
        "target_audience",
        "value_proposition",
        "constraints"
    ]
    
    completed = 0
    for field in fields:
        value = pv_data.get(field)
        if field == "constraints":
            if value and len(value) > 0:
                completed += 1
        else:
            if value and str(value).strip():
                completed += 1
    
    return int((completed / len(fields)) * 100)


def _truncate(text: str, max_length: int) -> str:
    """
    Truncate text to maximum length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def _render_field_metrics(field_key: str, value: Any):
    """
    Render metrics for a field.
    
    Args:
        field_key: Field identifier
        value: Field value
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if field_key == "constraints":
            count = len(value) if value else 0
            st.metric("Quantidade", count)
        else:
            length = len(str(value)) if value else 0
            st.metric("Caracteres", length)
    
    with col2:
        if field_key == "constraints":
            status = "✅ Definido" if value and len(value) > 0 else "❌ Pendente"
        else:
            status = "✅ Preenchido" if value and str(value).strip() else "❌ Vazio"
        st.metric("Status", status)
    
    with col3:
        # Quality indicator
        if field_key == "constraints":
            quality = "Bom" if value and len(value) >= 2 else "Melhorar"
        else:
            text_len = len(str(value)) if value else 0
            if text_len >= 50:
                quality = "Detalhado"
            elif text_len >= 20:
                quality = "Adequado"
            else:
                quality = "Básico"
        st.metric("Qualidade", quality)