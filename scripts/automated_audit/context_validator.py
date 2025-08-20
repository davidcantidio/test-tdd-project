#!/usr/bin/env python3
"""
🛡️ Context Validator - Quality Assurance for Context Extraction

Framework de validação de qualidade de contexto para o sistema de auditoria automatizada.
Garante que o contexto extraído atende aos padrões de qualidade antes da análise linha-por-linha.

Usage:
    python scripts/automated_audit/context_validator.py [options]

Features:
- Context completeness validation
- Cross-reference consistency checking  
- TDD+TDAH pattern verification
- Context quality metrics calculation
- Automated context quality scoring

Created: 2025-08-19 (Sétima Camada - Context Extraction System)
"""

import os
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import ast


class ContextQualityLevel(Enum):
    """Context quality classification levels."""
    EXCELLENT = "excellent"    # 90-100%
    GOOD = "good"             # 75-89%
    ACCEPTABLE = "acceptable" # 60-74%
    POOR = "poor"            # 40-59%
    INVALID = "invalid"      # 0-39%


class ContextType(Enum):
    """Types of context being validated."""
    TDD_WORKFLOW = "tdd_workflow"
    TDAH_OPTIMIZATION = "tdah_optimization"
    TECHNICAL_ARCHITECTURE = "technical_architecture"
    SECURITY_PATTERNS = "security_patterns"
    BUSINESS_LOGIC = "business_logic"
    INTEGRATION_POINTS = "integration_points"


@dataclass
class ContextValidationResult:
    """Result of context validation."""
    context_type: str
    quality_level: ContextQualityLevel
    quality_score: float
    completeness_score: float
    consistency_score: float
    relevance_score: float
    issues_found: List[str]
    recommendations: List[str]
    validation_details: Dict[str, Any]
    

@dataclass
class ContextValidationMetrics:
    """Metrics for context validation."""
    total_contexts_validated: int
    excellent_count: int
    good_count: int
    acceptable_count: int
    poor_count: int
    invalid_count: int
    average_quality_score: float
    critical_issues_count: int
    total_recommendations: int


class ContextValidator:
    """Main context validation framework."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize context validator."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.logger = logging.getLogger(f"{__name__}.ContextValidator")
        
        # Quality thresholds
        self.quality_thresholds = {
            ContextQualityLevel.EXCELLENT: 90.0,
            ContextQualityLevel.GOOD: 75.0,
            ContextQualityLevel.ACCEPTABLE: 60.0,
            ContextQualityLevel.POOR: 40.0,
            ContextQualityLevel.INVALID: 0.0
        }
        
        # Required TDD patterns
        self.required_tdd_patterns = [
            "Red.*Green.*Refactor",
            "TDD.*workflow", 
            "test.*first",
            "TDD.*integration",
            "cycle.*management"
        ]
        
        # Required TDAH patterns
        self.required_tdah_patterns = [
            "TDAH.*optimization",
            "focus.*session",
            "interruption.*handling",
            "hyperfocus.*protection",
            "energy.*tracking"
        ]
        
        # Required technical patterns
        self.required_technical_patterns = [
            "architecture.*pattern",
            "service.*layer",
            "database.*integration",
            "security.*implementation",
            "error.*handling"
        ]
        
        self.validation_results = []
        
    def validate_context_quality(self, context_content: str, context_type: ContextType) -> ContextValidationResult:
        """Validate quality of extracted context."""
        self.logger.info(f"Validating context quality for type: {context_type.value}")
        
        # Calculate individual scores
        completeness_score = self._calculate_completeness_score(context_content, context_type)
        consistency_score = self._calculate_consistency_score(context_content, context_type)
        relevance_score = self._calculate_relevance_score(context_content, context_type)
        
        # Calculate overall quality score
        quality_score = (completeness_score * 0.4 + consistency_score * 0.3 + relevance_score * 0.3)
        
        # Determine quality level
        quality_level = self._determine_quality_level(quality_score)
        
        # Find issues and generate recommendations
        issues = self._find_context_issues(context_content, context_type)
        recommendations = self._generate_recommendations(context_content, context_type, issues)
        
        # Create validation details
        validation_details = {
            "context_length": len(context_content),
            "word_count": len(context_content.split()),
            "line_count": len(context_content.splitlines()),
            "patterns_found": self._count_patterns(context_content, context_type),
            "cross_references": self._count_cross_references(context_content),
            "code_examples": self._count_code_examples(context_content),
            "validation_timestamp": self._get_timestamp()
        }
        
        result = ContextValidationResult(
            context_type=context_type.value,
            quality_level=quality_level,
            quality_score=quality_score,
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            relevance_score=relevance_score,
            issues_found=issues,
            recommendations=recommendations,
            validation_details=validation_details
        )
        
        self.validation_results.append(result)
        
        self.logger.info(f"Context validation complete: {quality_level.value} ({quality_score:.1f}%)")
        return result
    
    def _calculate_completeness_score(self, content: str, context_type: ContextType) -> float:
        """Calculate completeness score based on required patterns."""
        score = 0.0
        total_patterns = 0
        found_patterns = 0
        
        # Get required patterns based on context type
        if context_type == ContextType.TDD_WORKFLOW:
            patterns = self.required_tdd_patterns
        elif context_type == ContextType.TDAH_OPTIMIZATION:
            patterns = self.required_tdah_patterns
        elif context_type == ContextType.TECHNICAL_ARCHITECTURE:
            patterns = self.required_technical_patterns
        else:
            # For other types, use combination
            patterns = self.required_tdd_patterns + self.required_tdah_patterns
        
        total_patterns = len(patterns)
        
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns += 1
        
        if total_patterns > 0:
            score = (found_patterns / total_patterns) * 100
        
        # Bonus for comprehensive content
        if len(content.split()) > 1000:  # Long, detailed context
            score += 10
        if len(content.splitlines()) > 50:  # Well-structured content
            score += 5
        
        return min(score, 100.0)
    
    def _calculate_consistency_score(self, content: str, context_type: ContextType) -> float:
        """Calculate consistency score based on internal coherence."""
        score = 100.0  # Start with perfect score and deduct for issues
        
        # Check for conflicting information
        conflicts = self._find_conflicts(content)
        score -= len(conflicts) * 10
        
        # Check for broken cross-references
        broken_refs = self._find_broken_references(content)
        score -= len(broken_refs) * 5
        
        # Check for inconsistent terminology
        inconsistencies = self._find_terminology_inconsistencies(content)
        score -= len(inconsistencies) * 3
        
        # Bonus for well-structured content
        if self._has_clear_structure(content):
            score += 5
        
        return max(score, 0.0)
    
    def _calculate_relevance_score(self, content: str, context_type: ContextType) -> float:
        """Calculate relevance score based on context appropriateness."""
        score = 0.0
        
        # Check for context-specific keywords
        if context_type == ContextType.TDD_WORKFLOW:
            keywords = ["red", "green", "refactor", "test", "fail", "pass", "cycle"]
        elif context_type == ContextType.TDAH_OPTIMIZATION:
            keywords = ["focus", "attention", "interruption", "hyperfocus", "energy", "distraction"]
        elif context_type == ContextType.TECHNICAL_ARCHITECTURE:
            keywords = ["architecture", "pattern", "service", "layer", "component", "module"]
        else:
            keywords = ["tdd", "tdah", "workflow", "optimization", "pattern"]
        
        keyword_count = sum(1 for keyword in keywords if keyword.lower() in content.lower())
        score = (keyword_count / len(keywords)) * 100
        
        # Check for specific implementation details
        if self._has_implementation_details(content):
            score += 15
        
        # Check for examples and code snippets
        if self._has_code_examples(content):
            score += 10
        
        # Check for anti-patterns section
        if "anti-pattern" in content.lower():
            score += 10
        
        return min(score, 100.0)
    
    def _determine_quality_level(self, score: float) -> ContextQualityLevel:
        """Determine quality level based on score."""
        if score >= self.quality_thresholds[ContextQualityLevel.EXCELLENT]:
            return ContextQualityLevel.EXCELLENT
        elif score >= self.quality_thresholds[ContextQualityLevel.GOOD]:
            return ContextQualityLevel.GOOD
        elif score >= self.quality_thresholds[ContextQualityLevel.ACCEPTABLE]:
            return ContextQualityLevel.ACCEPTABLE
        elif score >= self.quality_thresholds[ContextQualityLevel.POOR]:
            return ContextQualityLevel.POOR
        else:
            return ContextQualityLevel.INVALID
    
    def _find_context_issues(self, content: str, context_type: ContextType) -> List[str]:
        """Find specific issues in context content."""
        issues = []
        
        # Check for missing critical sections
        if context_type == ContextType.TDD_WORKFLOW and "red-green-refactor" not in content.lower():
            issues.append("Missing core TDD cycle explanation")
        
        if context_type == ContextType.TDAH_OPTIMIZATION and "focus session" not in content.lower():
            issues.append("Missing TDAH focus session patterns")
        
        # Check for insufficient detail
        if len(content.split()) < 200:
            issues.append("Context too brief - needs more detail")
        
        # Check for missing code examples
        if not self._has_code_examples(content):
            issues.append("Missing code examples or implementation patterns")
        
        # Check for broken markdown formatting
        if self._has_broken_markdown(content):
            issues.append("Broken markdown formatting detected")
        
        # Check for outdated information
        if self._has_outdated_patterns(content):
            issues.append("Potentially outdated patterns or practices")
        
        return issues
    
    def _generate_recommendations(self, content: str, context_type: ContextType, issues: List[str]) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        # Address specific issues
        for issue in issues:
            if "too brief" in issue:
                recommendations.append("Add more detailed explanations and examples")
            elif "missing code examples" in issue:
                recommendations.append("Include practical code examples and usage patterns")
            elif "broken markdown" in issue:
                recommendations.append("Fix markdown formatting for better readability")
            elif "outdated patterns" in issue:
                recommendations.append("Update to current best practices and patterns")
        
        # General recommendations
        if context_type == ContextType.TDD_WORKFLOW:
            recommendations.append("Include specific TDD tools and framework integration")
        
        if context_type == ContextType.TDAH_OPTIMIZATION:
            recommendations.append("Add research-backed TDAH strategies and techniques")
        
        # Always recommend cross-references
        recommendations.append("Add cross-references to related documentation")
        
        return recommendations
    
    def _count_patterns(self, content: str, context_type: ContextType) -> Dict[str, int]:
        """Count various patterns in content."""
        patterns = {
            "tdd_patterns": len(re.findall(r'(?i)red.*green.*refactor|tdd.*cycle|test.*first', content)),
            "tdah_patterns": len(re.findall(r'(?i)focus.*session|hyperfocus|interruption.*handling', content)),
            "code_blocks": len(re.findall(r'```[\s\S]*?```', content)),
            "headings": len(re.findall(r'^#+\s', content, re.MULTILINE)),
            "lists": len(re.findall(r'^\s*[-*+]\s', content, re.MULTILINE)),
            "links": len(re.findall(r'\[.*?\]\(.*?\)', content))
        }
        return patterns
    
    def _count_cross_references(self, content: str) -> int:
        """Count cross-references to other documentation."""
        refs = re.findall(r'\[.*?\]\(.*?\.md\)', content)
        return len(refs)
    
    def _count_code_examples(self, content: str) -> int:
        """Count code examples in content."""
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        inline_code = re.findall(r'`[^`]+`', content)
        return len(code_blocks) + len(inline_code)
    
    def _find_conflicts(self, content: str) -> List[str]:
        """Find conflicting information in content."""
        # This is a simplified implementation
        # In practice, this would use more sophisticated NLP techniques
        conflicts = []
        
        # Check for obvious contradictions
        if "always use" in content.lower() and "never use" in content.lower():
            conflicts.append("Potential contradiction in usage guidelines")
        
        return conflicts
    
    def _find_broken_references(self, content: str) -> List[str]:
        """Find broken cross-references."""
        broken_refs = []
        
        # Extract markdown links
        links = re.findall(r'\[.*?\]\((.*?)\)', content)
        
        for link in links:
            if link.endswith('.md'):
                # Check if referenced file exists
                ref_path = self.project_root / link
                if not ref_path.exists():
                    broken_refs.append(f"Broken reference: {link}")
        
        return broken_refs
    
    def _find_terminology_inconsistencies(self, content: str) -> List[str]:
        """Find terminology inconsistencies."""
        inconsistencies = []
        
        # Check for common inconsistencies
        if "TDAH" in content and "ADHD" in content:
            inconsistencies.append("Mixed TDAH/ADHD terminology")
        
        if "TDD" in content and "Test Driven Development" in content:
            inconsistencies.append("Inconsistent TDD acronym usage")
        
        return inconsistencies
    
    def _has_clear_structure(self, content: str) -> bool:
        """Check if content has clear structure."""
        headings = re.findall(r'^#+\s', content, re.MULTILINE)
        return len(headings) >= 3  # At least 3 sections
    
    def _has_implementation_details(self, content: str) -> bool:
        """Check if content has implementation details."""
        implementation_indicators = [
            "implementation", "usage", "example", "pattern", 
            "class", "function", "method", "import"
        ]
        return any(indicator in content.lower() for indicator in implementation_indicators)
    
    def _has_code_examples(self, content: str) -> bool:
        """Check if content has code examples."""
        return bool(re.search(r'```[\s\S]*?```', content) or re.search(r'`[^`]+`', content))
    
    def _has_broken_markdown(self, content: str) -> bool:
        """Check for broken markdown formatting."""
        # Simple checks for common markdown issues
        issues = [
            re.search(r'#{5,}', content),  # Too many heading levels
            re.search(r'\[.*?\]\([^)]*$', content, re.MULTILINE),  # Unclosed links
            re.search(r'```[^`]*$', content, re.MULTILINE)  # Unclosed code blocks
        ]
        return any(issues)
    
    def _has_outdated_patterns(self, content: str) -> bool:
        """Check for potentially outdated patterns."""
        outdated_indicators = [
            "python 2", "legacy", "deprecated", "old version",
            "no longer", "obsolete"
        ]
        return any(indicator in content.lower() for indicator in outdated_indicators)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def validate_multiple_contexts(self, contexts: Dict[str, str]) -> ContextValidationMetrics:
        """Validate multiple contexts and return metrics."""
        self.logger.info(f"Validating {len(contexts)} contexts")
        
        results = []
        for context_name, content in contexts.items():
            # Determine context type from name/content
            context_type = self._determine_context_type(context_name, content)
            result = self.validate_context_quality(content, context_type)
            results.append(result)
        
        # Calculate metrics
        metrics = self._calculate_validation_metrics(results)
        
        self.logger.info(f"Validation complete: {metrics.average_quality_score:.1f}% average quality")
        return metrics
    
    def _determine_context_type(self, name: str, content: str) -> ContextType:
        """Determine context type from name and content."""
        name_lower = name.lower()
        content_lower = content.lower()
        
        if "tdd" in name_lower or "workflow" in name_lower:
            return ContextType.TDD_WORKFLOW
        elif "tdah" in name_lower or "focus" in content_lower:
            return ContextType.TDAH_OPTIMIZATION
        elif "security" in name_lower or "auth" in name_lower:
            return ContextType.SECURITY_PATTERNS
        elif "service" in name_lower or "architecture" in content_lower:
            return ContextType.TECHNICAL_ARCHITECTURE
        elif "business" in name_lower or "logic" in content_lower:
            return ContextType.BUSINESS_LOGIC
        else:
            return ContextType.INTEGRATION_POINTS
    
    def _calculate_validation_metrics(self, results: List[ContextValidationResult]) -> ContextValidationMetrics:
        """Calculate overall validation metrics."""
        total = len(results)
        if total == 0:
            return ContextValidationMetrics(0, 0, 0, 0, 0, 0, 0.0, 0, 0)
        
        # Count by quality level
        counts = {level: 0 for level in ContextQualityLevel}
        total_score = 0.0
        total_issues = 0
        total_recommendations = 0
        
        for result in results:
            counts[result.quality_level] += 1
            total_score += result.quality_score
            total_issues += len(result.issues_found)
            total_recommendations += len(result.recommendations)
        
        return ContextValidationMetrics(
            total_contexts_validated=total,
            excellent_count=counts[ContextQualityLevel.EXCELLENT],
            good_count=counts[ContextQualityLevel.GOOD],
            acceptable_count=counts[ContextQualityLevel.ACCEPTABLE],
            poor_count=counts[ContextQualityLevel.POOR],
            invalid_count=counts[ContextQualityLevel.INVALID],
            average_quality_score=total_score / total,
            critical_issues_count=total_issues,
            total_recommendations=total_recommendations
        )
    
    def generate_validation_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        if not self.validation_results:
            self.logger.warning("No validation results to report")
            return {}
        
        metrics = self._calculate_validation_metrics(self.validation_results)
        
        report = {
            "validation_summary": asdict(metrics),
            "validation_results": [asdict(result) for result in self.validation_results],
            "recommendations_summary": self._summarize_recommendations(),
            "quality_distribution": self._get_quality_distribution(),
            "generated_at": self._get_timestamp(),
            "validator_version": "1.0.0"
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Validation report saved to: {output_path}")
        
        return report
    
    def _summarize_recommendations(self) -> Dict[str, int]:
        """Summarize recommendations by type."""
        recommendations_count = {}
        for result in self.validation_results:
            for rec in result.recommendations:
                recommendations_count[rec] = recommendations_count.get(rec, 0) + 1
        return recommendations_count
    
    def _get_quality_distribution(self) -> Dict[str, float]:
        """Get quality level distribution percentages."""
        if not self.validation_results:
            return {}
        
        total = len(self.validation_results)
        distribution = {}
        
        for level in ContextQualityLevel:
            count = sum(1 for result in self.validation_results if result.quality_level == level)
            distribution[level.value] = (count / total) * 100
        
        return distribution


def main():
    """Main entry point for context validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Context Quality Validator")
    parser.add_argument("--context-file", help="Single context file to validate")
    parser.add_argument("--context-dir", help="Directory containing context files")
    parser.add_argument("--output-report", help="Output validation report path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    validator = ContextValidator()
    
    try:
        if args.context_file:
            # Validate single file
            with open(args.context_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            context_type = validator._determine_context_type(args.context_file, content)
            result = validator.validate_context_quality(content, context_type)
            
            print(f"✅ Context validation complete:")
            print(f"   Quality Level: {result.quality_level.value}")
            print(f"   Quality Score: {result.quality_score:.1f}%")
            print(f"   Issues Found: {len(result.issues_found)}")
            print(f"   Recommendations: {len(result.recommendations)}")
            
        elif args.context_dir:
            # Validate directory of files
            context_dir = Path(args.context_dir)
            contexts = {}
            
            for file_path in context_dir.glob("*.md"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    contexts[file_path.name] = f.read()
            
            metrics = validator.validate_multiple_contexts(contexts)
            
            print(f"✅ Multiple context validation complete:")
            print(f"   Total Contexts: {metrics.total_contexts_validated}")
            print(f"   Average Quality: {metrics.average_quality_score:.1f}%")
            print(f"   Excellent: {metrics.excellent_count}")
            print(f"   Good: {metrics.good_count}")
            print(f"   Acceptable: {metrics.acceptable_count}")
            print(f"   Poor: {metrics.poor_count}")
            print(f"   Invalid: {metrics.invalid_count}")
        
        # Generate report if requested
        if args.output_report:
            report = validator.generate_validation_report(Path(args.output_report))
            print(f"📊 Validation report saved to: {args.output_report}")
        
    except Exception as e:
        logging.error(f"Validation failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())