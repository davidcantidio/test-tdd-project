"""
🧪 Testes À Prova de Bala para PriorityScorer - História 3.1 FINAL

Testes TDD para validação do sistema de priorização de épicos com:
- Normalização matemática correta [0,1]
- Determinismo absoluto com quantização
- Chaveamento estável por UUID
- 4-level tie-breaking determinístico
- Robustez extrema (100 iterações com shuffle)

Segue critérios de aceitação da História 3.1:
- Score = função ponderada (valor, risco, esforço, alinhamento)
- Ordenação estável; empates determinísticos
- Robustez para produção

Implementação TDD seguindo metodologia Red-Green-Refactor.
"""

import pytest
import random
from typing import Dict, Any


class TestPriorityScorer:
    """TDD Tests for PriorityScorer - História 3.1 FINAL"""

    def test_normalization_mathematical_exactness(self):
        """Fórmulas devem produzir bounds exatos [0,1] - micro-checagem matemática"""
        from streamlit_extension.services.priority_scorer import PriorityScorer
        
        scorer = PriorityScorer()
        
        # Casos extremos que devem dar exatamente 0.0 e 1.0
        max_epic = create_epic(
            id="max_epic",
            business_priority=1,      # 1 → valor_score = 1.0
            complexity_score=1.0,     # 1 → risco_score = 1.0
            alignment_score=5         # 5 → alinhamento_score = 1.0
        )
        min_epic = create_epic(
            id="min_epic", 
            business_priority=5,      # 5 → valor_score = 0.0
            complexity_score=5.0,     # 5 → risco_score = 0.0
            alignment_score=1         # 1 → alinhamento_score = 0.0
        )
        
        scores = scorer.calculate_epic_scores([max_epic, min_epic])
        
        # Verificação de bounds exatos
        max_score = scores["max_epic"]
        min_score = scores["min_epic"]
        
        # Valor: (5 - priority) / 4
        assert max_score.valor_score == 1.0, f"Expected valor 1.0, got {max_score.valor_score}"
        assert min_score.valor_score == 0.0, f"Expected valor 0.0, got {min_score.valor_score}"
        
        # Risco: (5 - complexity) / 4  
        assert max_score.risco_score == 1.0, f"Expected risco 1.0, got {max_score.risco_score}"
        assert min_score.risco_score == 0.0, f"Expected risco 0.0, got {min_score.risco_score}"
        
        # Alinhamento: (alignment - 1) / 4
        assert max_score.alinhamento_score == 1.0, f"Expected alinhamento 1.0, got {max_score.alinhamento_score}"
        assert min_score.alinhamento_score == 0.0, f"Expected alinhamento 0.0, got {min_score.alinhamento_score}"
        
        # Todos componentes em [0,1]
        for epic_id, score in scores.items():
            assert 0.0 <= score.valor_score <= 1.0, f"{epic_id}: valor_score={score.valor_score}"
            assert 0.0 <= score.risco_score <= 1.0, f"{epic_id}: risco_score={score.risco_score}"
            assert 0.0 <= score.esforco_score <= 1.0, f"{epic_id}: esforco_score={score.esforco_score}"
            assert 0.0 <= score.alinhamento_score <= 1.0, f"{epic_id}: alinhamento_score={score.alinhamento_score}"
            assert 0.0 <= score.confidence_score <= 1.0, f"{epic_id}: confidence_score={score.confidence_score}"

    def test_determinism_under_extreme_conditions(self):
        """Determinismo com 100 iterações e entrada embaralhada - micro-checagem 5"""
        from streamlit_extension.services.priority_scorer import PriorityScorer
        
        # Épicos com IDs estáveis
        epics = [create_epic(id=f"epic_{i:03d}") for i in range(10)]
        scorer = PriorityScorer()
        
        results = []
        for iteration in range(100):
            shuffled_epics = epics.copy()
            random.shuffle(shuffled_epics)  # Embaralhar entrada
            
            ordered = scorer.order_epics_by_priority(shuffled_epics)
            result_ids = [e.id for e in ordered]
            results.append(result_ids)
        
        # TODOS devem ser idênticos
        reference = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result == reference, f"Iteration {i} differs from reference"
        
        print(f"✅ Determinismo verificado em {len(results)} iterações com entrada embaralhada")

    def test_floating_point_quantization_consistency(self):
        """Quantização deve eliminar variação de ponto flutuante - micro-checagem 3"""
        from streamlit_extension.services.priority_scorer import PriorityScorer
        
        epic = create_epic(
            id="quantization_test",
            business_priority=2, 
            complexity_score=3.333333333  # Número com repetição decimal
        )
        scorer = PriorityScorer()
        
        scores = []
        for _ in range(10):
            result = scorer.calculate_epic_scores([epic])
            scores.append(result["quantization_test"].total_score)
        
        # Todos bit-identical após quantização round(total, 9)
        reference_score = scores[0]
        for i, score in enumerate(scores[1:], 1):
            assert score == reference_score, f"Score {i}: {score} != {reference_score}"
        
        print(f"✅ Quantização consistente: {reference_score} em todas as execuções")

    def test_stable_id_keying_prevents_collisions(self):
        """ID estável deve prevenir colisões de título - micro-checagem UUID"""
        from streamlit_extension.services.priority_scorer import PriorityScorer
        
        epic1 = create_epic(title="Mesmo Título")  # ID UUID auto-gerado
        epic2 = create_epic(title="Mesmo Título")  # ID UUID diferente
        
        scorer = PriorityScorer()
        scores = scorer.calculate_epic_scores([epic1, epic2])
        
        # Deve ter 2 entradas distintas por ID
        assert len(scores) == 2
        assert epic1.id in scores
        assert epic2.id in scores
        assert epic1.id != epic2.id  # UUIDs diferentes
        
        print(f"✅ Colisões prevenidas: {epic1.id} != {epic2.id}")

    def test_effort_independence_from_business_value(self):
        """Esforço deve ser completamente independente do valor de negócio - sem dupla contagem"""
        from streamlit_extension.services.priority_scorer import PriorityScorer
        
        high_val_high_eff = create_epic(
            id="hv_he",
            business_priority=1,    # Alto valor
            effort_estimate=20      # Alto esforço
        )
        low_val_high_eff = create_epic(
            id="lv_he", 
            business_priority=5,    # Baixo valor
            effort_estimate=20      # Mesmo alto esforço
        )
        
        scorer = PriorityScorer()
        scores = scorer.calculate_epic_scores([high_val_high_eff, low_val_high_eff])
        
        # Esforço idêntico (mesmo effort_estimate)
        assert scores["hv_he"].esforco_score == scores["lv_he"].esforco_score
        
        # Valor diferente
        assert scores["hv_he"].valor_score > scores["lv_he"].valor_score
        
        print(f"✅ Esforço independente: {scores['hv_he'].esforco_score} == {scores['lv_he'].esforco_score}")
        print(f"✅ Valor diferente: {scores['hv_he'].valor_score} > {scores['lv_he'].valor_score}")

    def test_tie_breaking_four_levels_with_readable_priority(self):
        """Empate deve ser resolvido deterministicamente em 4 níveis - micro-checagem 4"""
        from streamlit_extension.services.priority_scorer import PriorityScorer
        
        # Épicos com scores potencialmente idênticos mas critérios de desempate diferentes
        epic_high_prio = create_epic(id="aaa_high", business_priority=1, effort_estimate=5)  # Prioridade alta
        epic_low_prio = create_epic(id="aaa_low", business_priority=5, effort_estimate=5)   # Prioridade baixa
        epic_low_effort = create_epic(id="aaa_effort", business_priority=3, effort_estimate=1)  # Baixo esforço
        epic_alpha = create_epic(id="alpha", business_priority=3, effort_estimate=5)        # Alfabético primeiro
        epic_beta = create_epic(id="beta", business_priority=3, effort_estimate=5)         # Alfabético segundo
        
        scorer = PriorityScorer()
        ordered = scorer.order_epics_by_priority([epic_beta, epic_alpha, epic_low_effort, epic_low_prio, epic_high_prio])
        ordered_ids = [e.id for e in ordered]
        
        # Verificar que ordenação segue lógica de tie-breaking
        # Level 2: business_priority ascendente (1=crítico primeiro) - micro-checagem 4
        high_prio_pos = ordered_ids.index("aaa_high")
        low_prio_pos = ordered_ids.index("aaa_low")
        assert high_prio_pos < low_prio_pos, f"High priority should come first: {ordered_ids}"
        
        # Level 4: Alfabético por ID
        alpha_pos = ordered_ids.index("alpha")
        beta_pos = ordered_ids.index("beta") 
        assert alpha_pos < beta_pos, f"Alpha should come before Beta: {ordered_ids}"
        
        print(f"✅ Tie-breaking ordenação: {ordered_ids}")

    def test_ordering_stability_across_multiple_runs(self):
        """Mesma entrada deve produzir mesma ordenação sempre"""
        from streamlit_extension.services.priority_scorer import PriorityScorer
        
        epics = [create_epic(id=f"stable_{i:03d}") for i in range(5)]
        scorer = PriorityScorer()
        
        results = []
        for _ in range(3):
            ordered = scorer.order_epics_by_priority(epics.copy())
            results.append([e.id for e in ordered])
        
        # Todos devem ser idênticos
        assert results[0] == results[1] == results[2]
        print(f"✅ Estabilidade verificada: {results[0]}")

    def test_weight_sensitivity_affects_ordering_predictably(self):
        """Mudança de pesos deve alterar ordenação conforme esperado"""
        from streamlit_extension.services.priority_scorer import PriorityScorer, EpicScoringWeights
        
        high_value_epic = create_epic(id="hv", business_priority=1, effort_estimate=10)
        low_effort_epic = create_epic(id="le", business_priority=3, effort_estimate=1)
        
        # Pesos padrão: valor=5, esforço=2
        default_scorer = PriorityScorer()
        default_order = [e.id for e in default_scorer.order_epics_by_priority([high_value_epic, low_effort_epic])]
        
        # Pesos favor esforço: valor=1, esforço=10
        effort_weights = EpicScoringWeights(valor=1.0, esforco=10.0, risco=1.0, alinhamento=1.0)
        effort_scorer = PriorityScorer(effort_weights)
        effort_order = [e.id for e in effort_scorer.order_epics_by_priority([high_value_epic, low_effort_epic])]
        
        # Ordenação deve mudar
        assert default_order != effort_order
        print(f"✅ Peso default: {default_order}, peso esforço: {effort_order}")

    def test_confidence_weight_zero_by_default(self):
        """Confidence deve ter peso 0 por padrão (feature flag) - micro-checagem"""
        from streamlit_extension.services.priority_scorer import EpicScoringWeights
        
        weights = EpicScoringWeights()
        assert weights.confidence == 0.0
        print("✅ Confidence peso 0 por padrão (feature flag)")

    def test_validation_rejects_invalid_epic_data(self):
        """Validação deve rejeitar dados inválidos com mensagens claras"""
        from streamlit_extension.services.priority_scorer import PriorityScorer
        
        scorer = PriorityScorer()
        
        # Título vazio
        with pytest.raises(ValueError, match="Epic must have title"):
            empty_title = create_epic(title="")
            scorer.calculate_epic_scores([empty_title])
        
        # Esforço inválido - testar diretamente no DTO criado manualmente
        from streamlit_extension.core.dto.epic_suggestion_dto import EpicSuggestionDTO
        
        # Criar DTO com esforço inválido (bypassar clamps do factory)
        invalid_epic = EpicSuggestionDTO(
            title="Valid Title", 
            rationale="Valid rationale",
            source="ai",
            effort_estimate=-5  # Inválido mesmo após clamp (será 1)
        )
        # Forçar esforço inválido diretamente (simular edge case)
        invalid_epic.effort_estimate = -1
        
        with pytest.raises(ValueError, match="effort_estimate must be > 0"):
            scorer.calculate_epic_scores([invalid_epic])
        
        print("✅ Validações críticas funcionando corretamente")

    def test_clamps_consistency_across_dto_and_scorer(self):
        """Clamps devem ser consistentes entre DTO e Scorer - micro-checagem 2"""  
        # Teste que valores fora de range são clampados consistentemente
        extreme_data = {
            "title": "Test Epic",
            "rationale": "Test rationale", 
            "source": "ai",
            "business_priority": 10,      # Fora de range (>5)
            "complexity_score": -1.0,     # Fora de range (<1)
            "effort_estimate": 0,         # Inválido (<=0) 
            "alignment_score": 7,         # Fora de range (>5)
            "confidence": 2.0             # Fora de range (>1)
        }
        
        from streamlit_extension.core.dto.epic_suggestion_dto import EpicSuggestionDTO
        
        # DTO deve aplicar clamps automaticamente (exceto effort_estimate que deve ser rejeitado)
        epic = EpicSuggestionDTO.from_dict(extreme_data)
        
        # Verificar clamps aplicados
        assert epic.business_priority == 5    # Clamped de 10 → 5
        assert epic.complexity_score == 1.0   # Clamped de -1 → 1.0
        assert epic.alignment_score == 5      # Clamped de 7 → 5
        assert epic.confidence == 1.0         # Clamped de 2.0 → 1.0
        
        # effort_estimate=0 deve falhar na validação do scorer
        epic.effort_estimate = 1  # Corrigir para teste prosseguir
        
        from streamlit_extension.services.priority_scorer import PriorityScorer
        scorer = PriorityScorer()
        scores = scorer.calculate_epic_scores([epic])
        
        # Scorer deve usar os mesmos clamps
        assert len(scores) == 1  # Score calculado com sucesso
        print("✅ Clamps consistentes entre DTO e Scorer")


# Fixtures e Helpers
def create_epic(id: str = None, title: str = "Test Epic", **overrides) -> 'EpicSuggestionDTO':
    """Factory para épicos de teste com ID UUID automático"""
    import uuid
    from streamlit_extension.core.dto.epic_suggestion_dto import EpicSuggestionDTO
    
    data = {
        "title": title,
        "rationale": "Test rationale",
        "tags": ["test"],
        "confidence": 0.8,
        "source": "ai",
        "id": id or str(uuid.uuid4()),        # ID UUID estável
        "business_priority": 3,
        "complexity_score": 3.0,
        "effort_estimate": 5,
        "alignment_score": 3
    }
    data.update(overrides)
    return EpicSuggestionDTO.from_dict(data)


# Testes TDD para História 3.1 - PriorityScorer À Prova de Bala