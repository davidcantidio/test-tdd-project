"""
🔍 Epic Explainers - História 4.2 Implementation

Epic explanation components for rationale/score breakdown visualization.
Implements formatters and services for História 4.2 acceptance criteria:
- Tooltip/expansão com rationale e breakdown do score
- Indicador de confiança da IA

Features:
- format_rationale: Sanitização, truncamento, fallbacks
- compute_score_breakdown: PriorityScorer integration, percentuais precisos
- format_confidence: Labels, cores, ranges (Baixa/Média/Alta)
- Cache integration: Performance otimizada com invalidação inteligente
- Security: Sanitização HTML, validação inputs, SQL injection prevention

Implementation follows TDD Green Phase methodology.
"""

import re
import hashlib
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import streamlit as st
from ..core.dto.epic_suggestion_dto import EpicSuggestionDTO
from ..services.priority_scorer import PriorityScorer, EpicPriorityScore


@dataclass
class ScoreBreakdown:
    """Estrutura para breakdown do score com percentuais"""
    percentages: Dict[str, float]  # percentuais por componente (0-100, 1 casa)
    raw_scores: Dict[str, float]   # scores brutos (0-1)
    total_score: float             # score total calculado
    
    
@dataclass 
class ConfidenceIndicator:
    """Estrutura para indicador de confiança"""
    label: str      # 'Baixa'|'Média'|'Alta'
    color: str      # código de cor hex ou nome
    value: float    # valor original da confidence (0-1)
    range: str      # range textual para tooltip


class EpicExplainerService:
    """
    Serviço para formatação de explicações de épicos.
    
    Implementa os contratos definidos no plano refinado:
    - format_rationale(texto, max_chars=500) -> str
    - compute_score_breakdown(epic, scorer) -> Dict[str, Any]
    - format_confidence(confidence) -> Dict[str, Any]
    """
    
    def __init__(self, cache_enabled: bool = True):
        """
        Inicializar serviço de explainers.
        
        Args:
            cache_enabled: Se deve usar cache para performance
        """
        self.cache_enabled = cache_enabled
    
    def format_rationale(self, texto: str, max_chars: int = 500) -> str:
        """
        Sanitiza rationale com truncamento inteligente.
        
        Args:
            texto: Rationale original
            max_chars: Limite de caracteres
            
        Returns:
            Rationale sanitizado e formatado
        """
        # Handle None/empty casos
        if texto is None or not isinstance(texto, str) or not texto.strip():
            return "Sem rationale fornecido"
        
        # Sanitização básica
        sanitized = self._sanitize_html_and_dangerous_chars(texto.strip())
        
        # Truncamento inteligente
        if len(sanitized) <= max_chars:
            return sanitized
        
        # Truncar e adicionar "...ver mais"
        truncated = sanitized[:max_chars].strip()
        
        # Evitar cortar no meio de uma palavra
        if max_chars < len(sanitized):
            last_space = truncated.rfind(' ')
            if last_space > max_chars * 0.8:  # Se não está muito longe
                truncated = truncated[:last_space]
        
        return f"{truncated}...ver mais"
    
    def compute_score_breakdown(self, epic: EpicSuggestionDTO, scorer: PriorityScorer) -> Dict[str, Any]:
        """
        Calcula breakdown do score com percentuais.
        
        Args:
            epic: Epic DTO com dados para scoring
            scorer: PriorityScorer configurado
            
        Returns:
            Dict com percentages, raw_scores, total_score
        """
        # Fallback para scorer None
        if scorer is None:
            return {
                'error': 'PriorityScorer não disponível',
                'fallback': True,
                'percentages': {'valor': 25.0, 'risco': 25.0, 'esforco': 25.0, 'alinhamento': 25.0},
                'raw_scores': {'valor': 0.25, 'risco': 0.25, 'esforco': 0.25, 'alinhamento': 0.25},
                'total_score': 3.0
            }
        
        # Gerar hash dos pesos para cache key
        weights_hash = self._hash_weights(scorer.weights)
        
        # Verificar cache primeiro
        cache_key = self.get_cache_key(epic.id, weights_hash)
        
        if self.cache_enabled:
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
        
        try:
            # Usar PriorityScorer para calcular scores
            scores_dict = scorer.calculate_epic_scores([epic])
            
            if epic.id not in scores_dict:
                return self._create_error_breakdown("Epic não encontrado nos scores")
            
            epic_score = scores_dict[epic.id]
            
            # Calcular percentuais baseados nos pesos do scorer
            weights = scorer.weights
            # Suportar duas convenções de nomes (valor vs valor_weight)
            def _w(obj, name: str) -> float:
                return float(getattr(obj, name, getattr(obj, f"{name}_weight", 0.0)))

            w_valor = _w(weights, 'valor')
            w_risco = _w(weights, 'risco')
            w_esforco = _w(weights, 'esforco')
            w_alinhamento = _w(weights, 'alinhamento')
            w_confidence = _w(weights, 'confidence')

            total_weight = (w_valor + w_risco + w_esforco + w_alinhamento + w_confidence)
            
            # Evitar divisão por zero
            if total_weight == 0:
                return self._create_error_breakdown("Pesos totais são zero")
            
            # Calcular percentuais (0-100 com 1 casa decimal) - POR PESO
            percentages_by_weight = {
                'valor': round((w_valor / total_weight) * 100, 1),
                'risco': round((w_risco / total_weight) * 100, 1),
                'esforco': round((w_esforco / total_weight) * 100, 1),
                'alinhamento': round((w_alinhamento / total_weight) * 100, 1)
            }

            # Adicionar confidence se peso > 0 (por peso)
            if w_confidence > 0:
                percentages_by_weight['confidence'] = round((w_confidence / total_weight) * 100, 1)
            
            # Raw scores
            raw_scores = {
                'valor': epic_score.valor_score,
                'risco': epic_score.risco_score,
                'esforco': epic_score.esforco_score,
                'alinhamento': epic_score.alinhamento_score,
                'confidence': epic_score.confidence_score
            }
            
            # Calcular percentuais POR CONTRIBUIÇÃO (peso * score)
            contrib_valor = w_valor * epic_score.valor_score
            contrib_risco = w_risco * epic_score.risco_score
            contrib_esforco = w_esforco * epic_score.esforco_score
            contrib_alinhamento = w_alinhamento * epic_score.alinhamento_score
            contrib_confidence = w_confidence * epic_score.confidence_score

            total_contrib = (
                contrib_valor + contrib_risco + contrib_esforco + contrib_alinhamento + contrib_confidence
            )

            if total_contrib <= 0:
                percentages_by_contribution = {
                    'valor': 25.0, 'risco': 25.0, 'esforco': 25.0, 'alinhamento': 25.0
                }
                if w_confidence > 0:
                    # Redistribuir para incluir confidence de forma simples
                    base = 100.0 / (4 + 1)
                    percentages_by_contribution = {
                        'valor': round(base, 1),
                        'risco': round(base, 1),
                        'esforco': round(base, 1),
                        'alinhamento': round(base, 1),
                        'confidence': round(base, 1)
                    }
            else:
                def pct(x: float) -> float:
                    return round((x / total_contrib) * 100, 1)

                percentages_by_contribution = {
                    'valor': pct(contrib_valor),
                    'risco': pct(contrib_risco),
                    'esforco': pct(contrib_esforco),
                    'alinhamento': pct(contrib_alinhamento)
                }
                if w_confidence > 0:
                    percentages_by_contribution['confidence'] = pct(contrib_confidence)

            result = {
                'percentages': percentages_by_weight,            # compat: por peso
                'contributions': percentages_by_contribution,    # novo: por contribuição
                'raw_scores': raw_scores,
                'total_score': epic_score.total_score
            }
            
            # Cachear resultado
            if self.cache_enabled:
                self._save_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            return self._create_error_breakdown(f"Erro no cálculo: {str(e)}")
    
    def format_confidence(self, confidence: Union[float, int, None]) -> Dict[str, Any]:
        """
        Formata indicador de confiança com cor e label.
        
        Args:
            confidence: Valor de confiança (0-1) ou inválido
            
        Returns:
            Dict com label, color, value, range
        """
        # Handle valores inválidos
        if confidence is None:
            confidence = 0.8  # Default padrão
        
        # Convert para float e clamp
        try:
            confidence_float = float(confidence)
        except (ValueError, TypeError):
            confidence_float = 0.8  # Default para valores não numéricos
        
        # Clamp para range válido
        confidence_float = max(0.0, min(1.0, confidence_float))
        
        # Determinar label e cor baseado em ranges
        if confidence_float <= 0.33:
            label = "Baixa"
            color = "#dc3545"  # Vermelho
            range_text = "[0.0-0.33]"
        elif confidence_float <= 0.66:
            label = "Média" 
            color = "#ffc107"  # Amarelo
            range_text = "[0.34-0.66]"
        else:
            label = "Alta"
            color = "#28a745"  # Verde
            range_text = "[0.67-1.0]"
        
        return {
            'label': label,
            'color': color,
            'value': confidence_float,
            'range': range_text
        }
    
    def get_cache_key(self, epic_id: str, weights_version: str) -> str:
        """
        Gera chave de cache para score breakdown.
        
        Args:
            epic_id: ID do épico
            weights_version: Versão dos pesos (para invalidação)
            
        Returns:
            Chave única para cache
        """
        key_data = f"{epic_id}_{weights_version}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def invalidate_cache(self, epic_id: Optional[str] = None):
        """
        Invalida cache para épico específico ou todos.
        
        Args:
            epic_id: ID do épico específico, None para todos
        """
        if not self.cache_enabled:
            return
        
        cache = self._get_cache_dict()
        
        if epic_id is None:
            # Limpar todo o cache
            cache.clear()
        else:
            # Para invalidar por epic_id, precisamos gerar todas as possíveis keys
            # Como não sabemos todos os pesos possíveis, vamos limpar tudo
            # (alternativa mais segura)
            # 
            # Uma implementação mais sofisticada poderia manter um mapeamento
            # reverso de epic_id -> keys, mas para simplicidade, limpamos tudo
            cache.clear()
    
    # === MÉTODOS PRIVADOS ===
    
    def _hash_weights(self, weights) -> str:
        """
        Gera hash único dos pesos para cache key.
        
        Args:
            weights: Objeto com pesos (valor, risco, esforco, alinhamento, confidence)
            
        Returns:
            String hash dos pesos
        """
        # Extrair valores dos pesos (suporta ambas convenções)
        def _w(obj, name: str) -> float:
            return float(getattr(obj, name, getattr(obj, f"{name}_weight", 0.0)))
        
        weights_dict = {
            'valor': _w(weights, 'valor'),
            'risco': _w(weights, 'risco'),
            'esforco': _w(weights, 'esforco'),
            'alinhamento': _w(weights, 'alinhamento'),
            'confidence': _w(weights, 'confidence')
        }
        
        # Criar string determinística dos pesos
        weights_json = json.dumps(weights_dict, sort_keys=True)
        
        # Gerar hash SHA256 truncado
        return hashlib.sha256(weights_json.encode()).hexdigest()[:16]
    
    def _sanitize_html_and_dangerous_chars(self, texto: str) -> str:
        """Sanitiza HTML e caracteres perigosos"""
        if not texto:
            return ""
        
        # Remove tags HTML perigosas
        dangerous_tags = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'<img[^>]*onerror[^>]*>',
            r'<style[^>]*>.*?</style>',
            r'<\?php.*?\?>',
            r'javascript:',
            r'on\w+\s*='
        ]
        
        sanitized = texto
        for pattern in dangerous_tags:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove todas as tags HTML restantes
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
        
        # Remove comandos SQL perigosos (case insensitive)
        sql_patterns = [
            r'\bDROP\s+TABLE\b',
            r'\bDELETE\s+FROM\b', 
            r'\bUNION\s+SELECT\b',
            r'\bOR\s+1\s*=\s*1\b',
            r'--\s*',
            r';.*?--'
        ]
        
        for pattern in sql_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    def _create_error_breakdown(self, error_msg: str) -> Dict[str, Any]:
        """Cria breakdown de fallback para erros"""
        return {
            'error': error_msg,
            'fallback': True,
            'percentages': {
                'valor': 25.0,
                'risco': 25.0,
                'esforco': 25.0,
                'alinhamento': 25.0
            },
            'raw_scores': {
                'valor': 0.25,
                'risco': 0.25,
                'esforco': 0.25,
                'alinhamento': 0.25,
                'confidence': 0.5
            },
            'total_score': 3.0
        }
    
    def _get_cache_dict(self) -> Dict[str, Any]:
        """Obtém dicionário de cache do session state"""
        try:
            # Try to access Streamlit session_state
            if not hasattr(st.session_state, '_epic_explainer_cache'):
                st.session_state._epic_explainer_cache = {}
            return st.session_state._epic_explainer_cache
        except Exception:
            # Fallback for tests or when Streamlit is not available
            # Use a class variable to share cache across instances during tests
            if not hasattr(EpicExplainerService, '_shared_test_cache'):
                EpicExplainerService._shared_test_cache = {}
            return EpicExplainerService._shared_test_cache
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Obtém resultado do cache"""
        try:
            cache = self._get_cache_dict()
            return cache.get(cache_key)
        except Exception:
            return None
    
    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Salva resultado no cache"""
        try:
            cache = self._get_cache_dict()
            cache[cache_key] = result
        except Exception:
            pass  # Ignore cache errors


# === SECURITY VALIDATION FUNCTIONS ===

def _validate_html_safe_string(value: str) -> str:
    """
    Valida que string é segura para uso em HTML.
    
    Args:
        value: String para validar
        
    Returns:
        String sanitizada ou vazia se inválida
    """
    if not value or not isinstance(value, str):
        return ""
    
    # Lista de padrões perigosos
    dangerous_patterns = [
        r'<script',
        r'<iframe',
        r'<object',
        r'<embed',
        r'<link',
        r'<meta',
        r'<style',
        r'javascript:',
        r'vbscript:',
        r'on\w+\s*=',
        r'<\?php',
        r'<%',
        r'{{',
        r'}}',
    ]
    
    # Verificar padrões perigosos (case insensitive)
    value_lower = value.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, value_lower):
            return ""
    
    # Remover caracteres de controle
    safe_value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    return safe_value.strip()


def _validate_color_value(color: str) -> str:
    """
    Valida valor de cor CSS.
    
    Args:
        color: Valor da cor (hex, nome, etc.)
        
    Returns:
        Cor validada ou cor padrão se inválida
    """
    if not color or not isinstance(color, str):
        return "#333333"
    
    # Validar cores hex
    hex_pattern = r'^#[0-9A-Fa-f]{3}$|^#[0-9A-Fa-f]{6}$'
    if re.match(hex_pattern, color):
        return color
    
    # Lista de cores CSS nomeadas válidas (básicas)
    valid_named_colors = {
        'red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink',
        'brown', 'black', 'white', 'gray', 'grey', 'cyan', 'magenta',
        'lime', 'maroon', 'navy', 'olive', 'teal', 'silver', 'aqua',
        'fuchsia', 'darkred', 'darkgreen', 'darkblue', 'darkgray',
        'darkgrey', 'lightgray', 'lightgrey', 'lightblue', 'lightgreen',
        'lightpink', 'lightyellow', 'lightcyan'
    }
    
    # Verificar se é cor nomeada válida
    if color.lower() in valid_named_colors:
        return color
    
    # Verificar se é cor RGB/RGBA válida
    rgb_pattern = r'^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(,\s*[\d.]+\s*)?\)$'
    if re.match(rgb_pattern, color):
        return color
    
    # Se não passou em nenhuma validação, usar cor padrão
    return "#333333"


# === UI COMPONENTS ===

def render_epic_explainer(epic: EpicSuggestionDTO, scorer: PriorityScorer) -> None:
    """
    Renderiza explainer completo para um épico.
    
    Args:
        epic: Epic DTO com dados
        scorer: PriorityScorer configurado
    """
    explainer = EpicExplainerService()
    
    # Format components
    rationale = explainer.format_rationale(epic.rationale)
    confidence_data = explainer.format_confidence(epic.confidence) 
    score_breakdown = explainer.compute_score_breakdown(epic, scorer)
    
    # Render rationale
    st.markdown("**📝 Justificativa:**")
    render_rationale_text(rationale)
    
    # Render confidence
    st.markdown("**🤖 Confiança IA:**")
    render_confidence_pill(confidence_data)
    
    # Render score breakdown
    st.markdown("**⚖️ Breakdown do Score:**")
    render_score_breakdown_table(score_breakdown)


def render_score_breakdown_table(breakdown: Dict[str, Any]) -> None:
    """
    Tabela com breakdown dos componentes do score.
    
    Args:
        breakdown: Resultado do compute_score_breakdown
    """
    if 'error' in breakdown:
        st.warning(f"⚠️ {breakdown['error']}")
        if not breakdown.get('fallback', False):
            return
    
    # Mostrar duas visões: por peso e por contribuição
    p_weight = breakdown.get('percentages', {})
    p_contrib = breakdown.get('contributions', {})

    weight_tab, contrib_tab = st.tabs(["⚖️ Por Peso", "🎯 Por Contribuição"])

    with weight_tab:
        # Tooltip explicativo para Por Peso
        st.info("ℹ️ **Por Peso:** Mostra a importância relativa de cada critério no algoritmo de priorização (baseado na configuração de pesos).")
        _render_percentages_metrics(p_weight)
        
    with contrib_tab:
        # Tooltip explicativo para Por Contribuição
        st.info("ℹ️ **Por Contribuição:** Mostra o impacto real de cada critério no score final deste épico específico (peso × score do épico).")
        _render_percentages_metrics(p_contrib)
    
    # Total score (opcional)
    if breakdown.get('total_score'):
        st.caption(f"Score Total: {breakdown['total_score']:.2f}")


def _render_percentages_metrics(percentages: Dict[str, Any]) -> None:
    """Renderiza métricas de percentuais em duas colunas"""
    if not percentages:
        st.info("Sem dados de percentuais")
        return
    col1, col2 = st.columns(2)
    with col1:
        if 'valor' in percentages:
            st.metric("💰 Valor", f"{float(percentages['valor']):.1f}%")
        if 'esforco' in percentages:
            st.metric("⚡ Esforço", f"{float(percentages['esforco']):.1f}%")
    with col2:
        if 'risco' in percentages:
            st.metric("⚠️ Risco", f"{float(percentages['risco']):.1f}%")
        if 'alinhamento' in percentages:
            st.metric("🎯 Alinhamento", f"{float(percentages['alinhamento']):.1f}%")
    if 'confidence' in percentages and float(percentages['confidence']) > 0:
        st.metric("🤖 Confiança IA", f"{float(percentages['confidence']):.1f}%")


def render_confidence_pill(confidence_data: Dict[str, Any]) -> None:
    """
    Pílula colorida com confiança da IA.
    
    Args:
        confidence_data: Resultado do format_confidence
    """
    label = confidence_data['label']
    color = confidence_data['color']
    value = confidence_data['value']
    range_text = confidence_data['range']
    
    # Validar valores para segurança HTML
    safe_label = _validate_html_safe_string(str(label))
    safe_color = _validate_color_value(str(color))
    safe_range = _validate_html_safe_string(str(range_text))
    safe_value = float(value) if isinstance(value, (int, float)) else 0.0
    
    # Fallback se validação falhou
    if not safe_label or not safe_color or not safe_range:
        st.warning("⚠️ Dados de confiança inválidos")
        return
    
    # CSS inline para pílula colorida (valores validados)
    pill_style = f"""
    <div style="
        display: inline-block;
        background-color: {safe_color};
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
        margin: 2px 0;
    ">
        {safe_label}: {safe_value:.2f} {safe_range}
    </div>
    """
    
    st.markdown(pill_style, unsafe_allow_html=True)


def render_rationale_text(rationale: str) -> None:
    """
    Texto do rationale com truncamento inteligente.
    
    Args:
        rationale: Rationale formatado
    """
    if "...ver mais" in rationale:
        # Rationale foi truncado
        base_text = rationale.replace("...ver mais", "")
        
        with st.expander("📖 Ver rationale completo"):
            st.write(base_text)
            st.info("💡 Rationale foi truncado na visualização resumida")
    else:
        # Rationale normal
        st.write(rationale)


# === CACHE UTILITIES ===

def get_score_cache(session_state) -> Dict[str, Any]:
    """
    Obtém cache de scores do session state.
    
    Args:
        session_state: Session state do Streamlit
        
    Returns:
        Dicionário de cache
    """
    if not hasattr(session_state, '_epic_explainer_cache'):
        session_state._epic_explainer_cache = {}
    return session_state._epic_explainer_cache


def should_recalculate(cache_key: str, epic_modified_time: str) -> bool:
    """
    Verifica se deve recalcular score baseado em timestamp.
    
    Args:
        cache_key: Chave do cache
        epic_modified_time: Timestamp de modificação do épico
        
    Returns:
        True se deve recalcular
    """
    # Lógica simplificada para GREEN phase
    # Pode ser expandida com timestamps reais
    return cache_key not in st.session_state.get('_epic_explainer_cache', {})
