"""
🧪 TDD Integration Tests for PriorityScorer with Custom Weights - História 3.2
Tests for PriorityScorer using project-specific weights from repository.

Following TDD Red-Green-Refactor methodology.
"""

import unittest
from unittest.mock import Mock, MagicMock
from typing import Optional

from streamlit_extension.services.priority_scorer import PriorityScorer, EpicScoringWeights
from streamlit_extension.core.dto.epic_suggestion_dto import EpicSuggestionDTO
from streamlit_extension.core.dto.priority_weights_dto import PriorityWeightsDTO
from streamlit_extension.services.priority_settings_repository import (
    PrioritySettingsRepository,
    InMemoryPrioritySettingsRepository
)


def create_test_epic(business_priority=3, complexity_score=3.0, 
                    effort_estimate=7, alignment_score=3, 
                    title="Test Epic") -> EpicSuggestionDTO:
    """Helper to create test epics"""
    return EpicSuggestionDTO(
        title=title,
        rationale=f"Rationale for {title}",
        business_priority=business_priority,
        complexity_score=complexity_score,
        effort_estimate=effort_estimate,
        alignment_score=alignment_score,
        source="test"
    )


class TestPriorityScorerWithCustomWeights(unittest.TestCase):
    """Integration tests for PriorityScorer with custom weight configurations"""
    
    def setUp(self):
        """Set up test repository and epics"""
        self.repository = InMemoryPrioritySettingsRepository()
        
        # Create test epics with different characteristics
        self.epic_high_value = create_test_epic(
            title="High Value Epic",
            business_priority=1,  # Highest priority
            complexity_score=3.0,
            effort_estimate=10,
            alignment_score=4
        )
        
        self.epic_low_effort = create_test_epic(
            title="Low Effort Epic",
            business_priority=3,
            complexity_score=2.0,
            effort_estimate=2,  # Very low effort
            alignment_score=3
        )
        
        self.epic_high_alignment = create_test_epic(
            title="High Alignment Epic",
            business_priority=2,
            complexity_score=4.0,
            effort_estimate=15,
            alignment_score=5  # Perfect alignment
        )
    
    def test_priority_scorer_uses_project_custom_weights(self):
        """Should use custom weights from repository when available"""
        # Given: Custom weights saved for project
        custom_weights = PriorityWeightsDTO(
            project_id=1,
            valor_weight=0.1,       # Low weight on business value
            risco_weight=0.1,       # Low weight on risk
            esforco_weight=0.7,     # HIGH weight on effort (efficiency focus)
            alinhamento_weight=0.1, # Low weight on alignment
            confidence_weight=0.0
        )
        self.repository.save(custom_weights)
        
        # When: Creating scorer with project_id
        scorer = PriorityScorer(
            1,  # project_id as first positional argument
            settings_repo=self.repository,
            total_scale=12.0
        )
        
        # Then: Scorer should use custom weights (scaled)
        # Custom weights scaled by 12.0: (0.1*12, 0.1*12, 0.7*12, 0.1*12)
        self.assertAlmostEqual(scorer.weights.valor, 1.2, places=1)
        self.assertAlmostEqual(scorer.weights.risco, 1.2, places=1)
        self.assertAlmostEqual(scorer.weights.esforco, 8.4, places=1)
        self.assertAlmostEqual(scorer.weights.alinhamento, 1.2, places=1)
        
        # And: Low effort epic should rank highest with effort-focused weights
        epics = [self.epic_high_value, self.epic_low_effort, self.epic_high_alignment]
        ordered = scorer.order_epics_by_priority(epics)
        
        # Low effort should be first due to 70% weight on effort efficiency
        self.assertEqual(ordered[0].title, "Low Effort Epic")
    
    def test_priority_scorer_uses_defaults_when_no_config(self):
        """Should fallback to default weights when no project config"""
        # Given: No custom weights saved for project
        # (repository is empty)
        
        # When: Creating scorer with project_id but no saved config
        scorer = PriorityScorer(
            999,  # Non-existent project as positional argument
            settings_repo=self.repository,
            total_scale=12.0
        )
        
        # Then: Should use default weights (5:3:2:2 proportion)
        self.assertAlmostEqual(scorer.weights.valor, 5.0, places=1)
        self.assertAlmostEqual(scorer.weights.risco, 3.0, places=1)
        self.assertAlmostEqual(scorer.weights.esforco, 2.0, places=1)
        self.assertAlmostEqual(scorer.weights.alinhamento, 2.0, places=1)
        
        # And: High value epic should rank highest with default weights
        epics = [self.epic_low_effort, self.epic_high_value, self.epic_high_alignment]
        ordered = scorer.order_epics_by_priority(epics)
        
        # High value should be first due to high weight on business value
        self.assertEqual(ordered[0].title, "High Value Epic")
    
    def test_normalized_weights_conversion(self):
        """Should convert normalized weights (≈0.4167,0.25,0.1667,0.1667) to absolute scale (×12.0)"""
        # Given: Default normalized weights
        normalized = PriorityWeightsDTO.get_defaults()
        
        # When: Creating scorer with default weights
        scorer = PriorityScorer(
            1,  # project_id as positional argument
            settings_repo=self.repository,  # Empty repo, will use defaults
            total_scale=12.0
        )
        
        # Then: Should convert to absolute scale correctly
        # 0.4167 * 12 ≈ 5.0
        # 0.25 * 12 = 3.0
        # 0.1667 * 12 ≈ 2.0
        # 0.1667 * 12 ≈ 2.0
        self.assertAlmostEqual(scorer.weights.valor, 5.0, places=0)
        self.assertAlmostEqual(scorer.weights.risco, 3.0, places=0)
        self.assertAlmostEqual(scorer.weights.esforco, 2.0, places=0)
        self.assertAlmostEqual(scorer.weights.alinhamento, 2.0, places=0)
        
        # Verify the exact scaling calculation
        expected_valor = normalized.valor_weight * 12.0
        expected_risco = normalized.risco_weight * 12.0
        self.assertAlmostEqual(scorer.weights.valor, expected_valor, places=3)
        self.assertAlmostEqual(scorer.weights.risco, expected_risco, places=3)
    
    def test_weight_changes_affect_epic_ordering(self):
        """Should reorder epics when weights change"""
        epics = [self.epic_high_value, self.epic_low_effort, self.epic_high_alignment]
        
        # Scenario 1: Value-focused weights
        value_weights = PriorityWeightsDTO(
            project_id=1,
            valor_weight=0.7,       # HIGH weight on value
            risco_weight=0.1,
            esforco_weight=0.1,
            alinhamento_weight=0.1,
            confidence_weight=0.0
        )
        self.repository.save(value_weights)
        
        scorer_value = PriorityScorer(
            1,  # project_id as positional argument
            settings_repo=self.repository,
            total_scale=12.0
        )
        ordered_value = scorer_value.order_epics_by_priority(epics)
        
        # High value epic should be first
        self.assertEqual(ordered_value[0].title, "High Value Epic")
        
        # Scenario 2: Alignment-focused weights
        alignment_weights = PriorityWeightsDTO(
            project_id=2,
            valor_weight=0.1,
            risco_weight=0.1,
            esforco_weight=0.1,
            alinhamento_weight=0.7,  # HIGH weight on alignment
            confidence_weight=0.0
        )
        self.repository.save(alignment_weights)
        
        scorer_alignment = PriorityScorer(
            2,  # project_id as positional argument
            settings_repo=self.repository,
            total_scale=12.0
        )
        ordered_alignment = scorer_alignment.order_epics_by_priority(epics)
        
        # High alignment epic should be first
        self.assertEqual(ordered_alignment[0].title, "High Alignment Epic")
        
        # Scenario 3: Effort-focused weights (already tested above)
        effort_weights = PriorityWeightsDTO(
            project_id=3,
            valor_weight=0.1,
            risco_weight=0.1,
            esforco_weight=0.7,      # HIGH weight on effort
            alinhamento_weight=0.1,
            confidence_weight=0.0
        )
        self.repository.save(effort_weights)
        
        scorer_effort = PriorityScorer(
            3,  # project_id as positional argument
            settings_repo=self.repository,
            total_scale=12.0
        )
        ordered_effort = scorer_effort.order_epics_by_priority(epics)
        
        # Low effort epic should be first
        self.assertEqual(ordered_effort[0].title, "Low Effort Epic")
        
        # Verify all three orderings are different
        order1 = [e.title for e in ordered_value]
        order2 = [e.title for e in ordered_alignment]
        order3 = [e.title for e in ordered_effort]
        
        self.assertNotEqual(order1, order2)
        self.assertNotEqual(order2, order3)
        self.assertNotEqual(order1, order3)


class TestPriorityScorerBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing code"""
    
    def test_scorer_works_without_repository(self):
        """Should work with default weights when no repository provided"""
        # Given: No repository or project_id
        # When: Creating scorer the old way
        scorer = PriorityScorer()  # No parameters
        
        # Then: Should use default weights from História 3.1
        self.assertEqual(scorer.weights.valor, 5.0)
        self.assertEqual(scorer.weights.risco, 3.0)
        self.assertEqual(scorer.weights.esforco, 2.0)
        self.assertEqual(scorer.weights.alinhamento, 2.0)
        self.assertEqual(scorer.weights.confidence, 0.0)
    
    def test_scorer_works_with_explicit_weights(self):
        """Should use explicitly provided weights over repository"""
        # Given: Custom weights and a repository with different weights
        repo = InMemoryPrioritySettingsRepository()
        repo_weights = PriorityWeightsDTO(
            project_id=1,
            valor_weight=0.1,
            risco_weight=0.1,
            esforco_weight=0.7,
            alinhamento_weight=0.1,
            confidence_weight=0.0
        )
        repo.save(repo_weights)
        
        explicit_weights = EpicScoringWeights(
            valor=10.0,
            risco=1.0,
            esforco=1.0,
            alinhamento=0.0,
            confidence=0.0
        )
        
        # When: Creating scorer with explicit weights
        scorer = PriorityScorer(
            1,  # project_id as positional argument  
            weights=explicit_weights,  # Explicit weights take precedence
            settings_repo=repo
        )
        
        # Then: Should use explicit weights, not repository weights
        self.assertEqual(scorer.weights.valor, 10.0)
        self.assertEqual(scorer.weights.risco, 1.0)
        self.assertEqual(scorer.weights.esforco, 1.0)
        self.assertEqual(scorer.weights.alinhamento, 0.0)


if __name__ == '__main__':
    unittest.main()