"""
Steps mode utilities for Product Vision.

This module provides utilities specific to the steps mode
of the Product Vision wizard.
"""

from typing import Dict, Any
import streamlit as st


def get_field_progress_message(field_key: str, field_label: str) -> str:
    """
    Get a progress message for a specific field.
    
    Args:
        field_key: The field identifier
        field_label: The human-readable field label
        
    Returns:
        Progress message string
    """
    messages = {
        "vision_statement": f"📝 Definindo a visão do produto...",
        "problem_statement": f"🎯 Identificando o problema a resolver...",
        "target_audience": f"👥 Especificando o público-alvo...",
        "value_proposition": f"💎 Elaborando a proposta de valor...",
        "constraints": f"⚠️ Listando as restrições do projeto..."
    }
    return messages.get(field_key, f"✍️ Preenchendo {field_label}...")


def get_field_completion_icon(field_key: str, value: Any) -> str:
    """
    Get an icon indicating the completion status of a field.
    
    Args:
        field_key: The field identifier
        value: The current value of the field
        
    Returns:
        Icon string
    """
    if field_key == "constraints":
        if value and len(value) > 0:
            return "✅"
        else:
            return "⏳"
    else:
        if value and str(value).strip():
            return "✅"
        else:
            return "⏳"


def render_field_tips(field_key: str):
    """
    Render helpful tips for filling out a specific field.
    
    Args:
        field_key: The field identifier
    """
    tips = {
        "vision_statement": [
            "💡 Seja claro e inspirador",
            "💡 Foque no impacto desejado",
            "💡 Mantenha entre 50-150 caracteres"
        ],
        "problem_statement": [
            "💡 Seja específico sobre o problema",
            "💡 Mencione quem é afetado",
            "💡 Quantifique o impacto quando possível"
        ],
        "target_audience": [
            "💡 Defina características demográficas",
            "💡 Inclua necessidades específicas",
            "💡 Considere segmentação"
        ],
        "value_proposition": [
            "💡 Destaque o diferencial",
            "💡 Foque nos benefícios",
            "💡 Seja conciso e direto"
        ],
        "constraints": [
            "💡 Liste uma restrição por linha",
            "💡 Seja específico (ex: 'Orçamento: R$ 50.000')",
            "💡 Inclua prazos, recursos e limitações técnicas"
        ]
    }
    
    if field_key in tips:
        with st.expander("💡 Dicas para este campo", expanded=False):
            for tip in tips[field_key]:
                st.caption(tip)