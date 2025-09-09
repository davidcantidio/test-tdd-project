"""Utilidades do modo Formulário (Product Vision).


- Este arquivo contém funções que ajudam a verificar se você preencheu
  bem os campos do formulário e a mostrar dicas claras sobre o que ainda
  falta melhorar. Ele não salva nada em banco; apenas analisa o texto e
  exibe feedback visual (barras de progresso e avisos).
"""

from typing import Dict, Any, List, Tuple
import streamlit as st


def validate_all_fields(pv_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Valida todos os campos e retorna feedback simples.

    Parâmetro:
        pv_data: dicionário com os 5 campos da Product Vision.

    Retorno:
        (ok, problemas):
        - ok: True se tudo parece preenchido de forma mínima.
        - problemas: lista de mensagens objetivas do que falta melhorar.
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
        
    # Check constraints (string multilinhas: 1 por linha)
    constraints = pv_data.get("constraints", "")
    constraints = str(constraints).strip()
    if not constraints:
        issues.append("Nenhuma restrição definida")
    elif len([ln for ln in constraints.splitlines() if ln.strip()]) < 2:
        issues.append("Defina pelo menos 2 restrições do projeto (uma por linha)")
        
    return len(issues) == 0, issues


def render_validation_feedback(pv_data: Dict[str, Any]) -> None:
    """Mostra um resumo do que está bom e do que precisa de atenção.

    Parâmetro:
        pv_data: dicionário com os campos preenchidos pelo usuário.
    """
    is_valid, issues = validate_all_fields(pv_data)
    
    if is_valid:
        st.success("✅ Todos os campos estão preenchidos corretamente!")
    else:
        with st.expander(f"⚠️ {len(issues)} campo(s) precisam de atenção", expanded=True):
            for issue in issues:
                st.warning(f"• {issue}")


def get_field_quality_score(field_key: str, value: Any) -> int:
    """Calcula uma nota (0–100) simples para cada campo.

    Ideia: textos um pouco maiores e bem escritos ganham mais pontos. Para
    `constraints`, consideramos a quantidade de linhas com conteúdo.
    """
    if field_key == "constraints":
        text = str(value or "").strip()
        if not text:
            return 0
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        # Até 60 pts pela quantidade de restrições
        score = min(len(lines) * 20, 60)
        # +20 pts se a média de caracteres por linha for razoável (>= 15)
        if lines:
            avg_len = sum(len(ln) for ln in lines) / len(lines)
            if avg_len >= 15:
                score += 20
        # +20 pts se houver sinais de pontuação básica em alguma linha
        if any(any(p in ln for p in ".!?;") for ln in lines):
            score += 20
        return min(score, 100)

    # Demais campos (texto livre)
    text = str(value or "").strip()
    if not text:
        return 0

    score = 0
    # Comprimento
    if len(text) >= 10:
        score += 20
    if len(text) >= 30:
        score += 20
    if len(text) >= 50:
        score += 20
    # Qualidade simples
    if any(p in text for p in ".!?;"):
        score += 10  # tem pontuação
    if len(text.split()) >= 5:
        score += 15  # várias palavras
    # Primeira letra maiúscula ajuda na legibilidade
    if text[:1].isupper():
        score += 15
    return min(score, 100)


def render_quality_indicators(pv_data: Dict[str, Any]) -> None:
    """Mostra barras simples de qualidade para cada campo.

    É apenas um indicativo visual para ajudar a revisar o texto.
    Não substitui decisão humana nem validação de negócio.
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
        
        # Sinalização simples por ícone
        if score >= 80:
            icon = "✅"
        elif score >= 50:
            icon = "⚠️"
        else:
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
