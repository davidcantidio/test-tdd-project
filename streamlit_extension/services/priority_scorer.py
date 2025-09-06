"""
🎯 PriorityScorer - História 3.1 + 3.2 ENHANCED

Epic priority scoring with mathematically correct normalization,
stable UUID keying, deterministic tie-breaking, and project-specific weights.

Features:
- All components normalized to [0,1] with corrected formulas
- No double counting of business value in effort
- Deterministic tie-breaking (score → priority → effort → UUID)
- Robust validation with clear error messages
- Quantization for floating point determinism
- Clean architecture with DTO imports from core
- História 3.2: Project-specific weight configuration via DI

Implementação à prova de bala para produção enterprise.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from ..core.dto.epic_suggestion_dto import EpicSuggestionDTO  # ✅ Clean import (micro-checagem 1)
from ..core.dto.priority_weights_dto import PriorityWeightsDTO  # História 3.2

# Avoid circular imports
if TYPE_CHECKING:
    from .priority_settings_repository import PrioritySettingsRepository


@dataclass(frozen=True)
class EpicScoringWeights:
    """Balanced weights for epic prioritization (post-normalization)"""
    valor: float = 5.0          # Business value (highest priority)
    risco: float = 3.0          # Risk mitigation importance
    esforco: float = 2.0        # Effort efficiency preference  
    alinhamento: float = 2.0    # Strategic alignment importance
    confidence: float = 0.0     # AI confidence bonus (feature flag OFF - micro-checagem)


@dataclass
class EpicPriorityScore:
    """Epic priority score breakdown with normalized components [0,1]"""
    epic_key: str
    total_score: float          # Quantized for determinism
    valor_score: float          # [0,1] Business priority score
    risco_score: float          # [0,1] Risk score (inverted complexity)
    esforco_score: float        # [0,1] Effort efficiency (no double counting)
    alinhamento_score: float    # [0,1] Strategic alignment score  
    confidence_score: float     # [0,1] AI confidence score


class PriorityScorer:
    """
    Epic priority scorer with mathematically correct implementation and project-specific weights.
    
    Features:
    - Normalized components [0,1] with corrected formulas (micro-checagem fórmulas)
    - Stable UUID keying (no title collisions)  
    - Deterministic tie-breaking with quantization (micro-checagem 3)
    - Readable priority ordering (micro-checagem 4)
    - Consistent clamps throughout (micro-checagem 2)
    - Robust validation with clear error messages
    - História 3.2: Project-specific weight configuration via DI
    """
    
    def __init__(self, 
                 project_id_or_weights=None,
                 weights: Optional[EpicScoringWeights] = None,
                 settings_repo: Optional['PrioritySettingsRepository'] = None,
                 total_scale: float = 12.0):
        """
        Initialize PriorityScorer with flexible weight configuration.
        
        Args:
            project_id_or_weights: Can be either:
                                 - int: project ID for loading custom weights
                                 - EpicScoringWeights: explicit weights (História 3.1 compatibility)
                                 - None: use defaults
            weights: Explicit weights (takes precedence, História 3.2 style)
            settings_repo: Repository for loading project-specific weights
            total_scale: Scale factor for converting normalized weights to absolute
        
        Priority order:
        1. Explicit weights parameter (if provided)
        2. EpicScoringWeights as first parameter (História 3.1 compatibility)
        3. Project-specific weights from repository (if project_id and repo provided)  
        4. Default weights (5:3:2:2 proportion)
        """
        # Handle backward compatibility with História 3.1
        if isinstance(project_id_or_weights, EpicScoringWeights):
            # História 3.1 style: PriorityScorer(EpicScoringWeights)
            self.weights = project_id_or_weights
        elif weights is not None:
            # História 3.2 explicit style: PriorityScorer(weights=EpicScoringWeights)
            self.weights = weights
        elif isinstance(project_id_or_weights, int) and settings_repo is not None:
            # História 3.2 DI style: PriorityScorer(project_id=1, settings_repo=repo)
            project_weights = settings_repo.get_by_project_id(project_id_or_weights)
            if project_weights:
                self.weights = self._convert_to_absolute_weights(project_weights, total_scale)
            else:
                # No custom weights, use defaults
                self.weights = self._get_default_absolute_weights(total_scale)
        else:
            # Default: use História 3.1 defaults
            self.weights = EpicScoringWeights()
    
    def _convert_to_absolute_weights(self, normalized: PriorityWeightsDTO, total_scale: float) -> EpicScoringWeights:
        """
        Convert normalized weights [0,1] to absolute scale for computation.
        
        The total_scale of 12.0 preserves the 5:3:2:2 proportion from História 3.1.
        
        Args:
            normalized: Normalized weights from repository (sum ≈ 1.0)
            total_scale: Scale factor for conversion (default 12.0)
            
        Returns:
            EpicScoringWeights with absolute values
        """
        return EpicScoringWeights(
            valor=normalized.valor_weight * total_scale,
            risco=normalized.risco_weight * total_scale,
            esforco=normalized.esforco_weight * total_scale,
            alinhamento=normalized.alinhamento_weight * total_scale,
            confidence=normalized.confidence_weight * total_scale
        )
    
    def _get_default_absolute_weights(self, total_scale: float) -> EpicScoringWeights:
        """
        Get default weights in absolute scale.
        
        Uses PriorityWeightsDTO defaults (preserving 5:3:2:2 proportion).
        
        Args:
            total_scale: Scale factor for conversion
            
        Returns:
            EpicScoringWeights with default values scaled
        """
        defaults = PriorityWeightsDTO.get_defaults()
        return self._convert_to_absolute_weights(defaults, total_scale)
    
    def calculate_epic_scores(self, epics: List[EpicSuggestionDTO]) -> Dict[str, EpicPriorityScore]:
        """Calculate priority scores with stable UUID keying"""
        scores = {}
        
        for epic in epics:
            self._validate_epic(epic)
            
            # Normalized components [0,1] - fórmulas corrigidas (micro-checagem matemática)
            valor = self._calculate_valor_score(epic)
            risco = self._calculate_risco_score(epic)
            esforco = self._calculate_esforco_score(epic)
            alinhamento = self._calculate_alinhamento_score(epic)
            confidence = self._calculate_confidence_score(epic)
            
            # Weighted total com quantização (micro-checagem 3)
            total = (
                self.weights.valor * valor +
                self.weights.risco * risco +
                self.weights.esforco * esforco +
                self.weights.alinhamento * alinhamento +
                self.weights.confidence * confidence
            )
            
            scores[epic.id] = EpicPriorityScore(
                epic_key=epic.id,
                total_score=round(total, 9),  # ✅ Quantização para determinismo absoluto
                valor_score=valor,
                risco_score=risco,
                esforco_score=esforco,
                alinhamento_score=alinhamento,
                confidence_score=confidence
            )
        
        return scores
    
    def order_epics_by_priority(self, epics: List[EpicSuggestionDTO]) -> List[EpicSuggestionDTO]:
        """Order epics with deterministic tie-breaking"""
        scores = self.calculate_epic_scores(epics)
        return sorted(epics, key=lambda e: self._priority_tuple(e, scores[e.id]))
    
    def _validate_epic(self, epic: EpicSuggestionDTO) -> None:
        """Validate epic with clear error messages"""
        if not epic.title or not epic.title.strip():
            raise ValueError("Epic must have title")
        
        if epic.effort_estimate <= 0:
            raise ValueError(f"effort_estimate must be > 0, got {epic.effort_estimate}")
        
        if not epic.id or not epic.id.strip():
            raise ValueError("Epic must have ID")
    
    def _calculate_valor_score(self, epic: EpicSuggestionDTO) -> float:
        """Business value [0,1]: priority 1→1.0, 5→0.0 (fórmula corrigida)"""
        priority = max(1, min(5, epic.business_priority))  # Clamp consistente (micro-checagem 2)
        return (5 - priority) / 4  # ✅ CORRIGIDO: 1→1.0, 5→0.0
    
    def _calculate_risco_score(self, epic: EpicSuggestionDTO) -> float:
        """Risk [0,1]: complexity 1→1.0, 5→0.0 (lower complexity = higher score)"""
        complexity = max(1.0, min(5.0, epic.complexity_score))  # Clamp consistente
        return (5 - complexity) / 4  # ✅ CORRIGIDO: 1→1.0, 5→0.0
    
    def _calculate_esforco_score(self, epic: EpicSuggestionDTO) -> float:
        """Effort efficiency [0,1]: independent of business value (no double counting)"""
        effort_days = max(1, epic.effort_estimate)  # Clamp consistente
        return 1 / (1 + effort_days)  # ✅ Sem dupla contagem, bounded (0,1)
    
    def _calculate_alinhamento_score(self, epic: EpicSuggestionDTO) -> float:
        """Alignment [0,1]: alignment 1→0.0, 5→1.0 (fórmula corrigida)"""
        alignment = max(1, min(5, epic.alignment_score))  # Clamp consistente
        return (alignment - 1) / 4  # ✅ CORRIGIDO: 1→0.0, 5→1.0
    
    def _calculate_confidence_score(self, epic: EpicSuggestionDTO) -> float:
        """AI confidence [0,1]: already normalized"""
        return max(0.0, min(1.0, epic.confidence))  # Clamp consistente
    
    def _priority_tuple(self, epic: EpicSuggestionDTO, score: EpicPriorityScore) -> Tuple[float, int, int, str]:
        """4-level deterministic tie-breaking (legível - micro-checagem 4)"""
        business_priority = max(1, min(5, epic.business_priority))
        effort_days = max(1, epic.effort_estimate)
        
        return (
            -round(score.total_score, 9),  # Level 1: Higher score first (quantizado)
            business_priority,             # Level 2: Lower priority number first (1=crítico) ✅ Legível
            effort_days,                   # Level 3: Lower effort first (quick wins)
            epic.id                        # Level 4: Alphabetical by UUID (deterministic)
        )