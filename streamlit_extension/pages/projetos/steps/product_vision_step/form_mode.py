"""
Form mode utilities for Product Vision.

This module provides utilities specific to the form mode
of the Product Vision wizard.
"""

from typing import Dict, Any, List, Tuple
import streamlit as st


def validate_all_fields(pv_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate all Product Vision fields and return detailed feedback.
    
    Args:
        pv_data: Dictionary with Product Vision data
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check vision statement
    if not pv_data.get("vision_statement", "").strip():
        issues.append("Declaração de Visão está vazia")
    elif len(pv_data.get("vision_statement", "")) < 10:
        issues.append("Declaração de Visão muito curta (mínimo 10 caracteres)")
        
    # Check problem statement
    if not pv_data.get("problem_statement", "").strip():
        issues.append("Declaração do Problema está vazia")
    elif len(pv_data.get("problem_statement", "")) < 20:
        issues.append("Declaração do Problema muito curta (mínimo 20 caracteres)")
        
    # Check target audience
    if not pv_data.get("target_audience", "").strip():
        issues.append("Público-alvo não definido")
        
    # Check value proposition
    if not pv_data.get("value_proposition", "").strip():
        issues.append("Proposta de Valor está vazia")
        
    # Check constraints
    constraints = pv_data.get("constraints", [])
    if not constraints or len(constraints) == 0:
        issues.append("Nenhuma restrição definida")
    elif len(constraints) < 2:
        issues.append("Defina pelo menos 2 restrições do projeto")
        
    return len(issues) == 0, issues


def render_validation_feedback(pv_data: Dict[str, Any]):
    """
    Render validation feedback for the form.
    
    Args:
        pv_data: Dictionary with Product Vision data
    """
    is_valid, issues = validate_all_fields(pv_data)
    
    if is_valid:
        st.success("✅ Todos os campos estão preenchidos corretamente!")
    else:
        with st.expander(f"⚠️ {len(issues)} campo(s) precisam de atenção", expanded=True):
            for issue in issues:
                st.warning(f"• {issue}")


def get_field_quality_score(field_key: str, value: Any) -> int:
    """
    Calculate a quality score for a field value.
    
    Args:
        field_key: The field identifier
        value: The field value
        
    Returns:
        Score from 0 to 100
    """
    if field_key == "constraints":
        if not value:
            return 0
        # Score based on number and quality of constraints
        score = min(len(value) * 20, 60)  # Up to 60 points for having constraints
        # Add points for well-formatted constraints
        for constraint in value:
            if len(constraint) > 10:
                score += 10
        return min(score, 100)
    else:
        if not value or not str(value).strip():
            return 0
        
        text = str(value).strip()
        score = 0
        
        # Length scoring
        if len(text) >= 10:
            score += 20
        if len(text) >= 30:
            score += 20
        if len(text) >= 50:
            score += 20
            
        # Quality indicators
        if "." in text or "!" in text or "?" in text:
            score += 10  # Has punctuation
        if len(text.split()) >= 5:
            score += 15  # Multiple words
        if any(c.isupper() for c in text[1:]):
            score += 15  # Proper capitalization
            
        return min(score, 100)


def render_quality_indicators(pv_data: Dict[str, Any]):
    """
    Render quality indicators for all fields.
    
    Args:
        pv_data: Dictionary with Product Vision data
    """
    st.markdown("### 📊 Qualidade do Preenchimento")
    
    field_labels = {
        "vision_statement": "Declaração de Visão",
        "problem_statement": "Problema a Resolver",
        "target_audience": "Público-alvo",
        "value_proposition": "Proposta de Valor",
        "constraints": "Restrições"
    }
    
    total_score = 0
    field_count = 0
    
    for field_key, label in field_labels.items():
        score = get_field_quality_score(field_key, pv_data.get(field_key))
        total_score += score
        field_count += 1
        
        # Color based on score
        if score >= 80:
            color = "green"
            icon = "✅"
        elif score >= 50:
            color = "orange"
            icon = "⚠️"
        else:
            color = "red"
            icon = "❌"
            
        st.progress(score / 100, text=f"{icon} {label}: {score}%")
    
    # Overall score
    overall_score = total_score // field_count if field_count > 0 else 0
    
    if overall_score >= 80:
        st.success(f"🎉 Qualidade Geral: {overall_score}% - Excelente!")
    elif overall_score >= 60:
        st.info(f"📈 Qualidade Geral: {overall_score}% - Bom, mas pode melhorar")
    else:
        st.warning(f"⚠️ Qualidade Geral: {overall_score}% - Precisa de mais detalhes")