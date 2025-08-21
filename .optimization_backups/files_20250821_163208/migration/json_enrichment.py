#!/usr/bin/env python3
"""
✨ JSON Enrichment Engine for Epic-Database Sync

Enriquece JSONs de épicos com campos calculados sem modificar dados originais.
Implementa a estratégia de 3 camadas:

CAMADA 1: Core Data (JSON ↔ Database) - Sync bidirecional
CAMADA 2: Calculated Fields (Database → JSON) - Enriquecimento apenas  
CAMADA 3: System Fields (Database Only) - Nunca exportados

Exemplo de saída:
{
  "epic": { ... dados originais ... },
  "calculated_fields": {
    "planned_start_date": "2025-08-18",
    "planned_end_date": "2025-08-20", 
    "calculated_duration_days": 2.0,
    "last_calculated": "2025-08-14T10:30:00"
  },
  "metadata": {
    "version": "v1.0",
    "enriched_at": "2025-08-14T10:30:00",
    "calculation_strategy": "next_monday"
  }
}
"""

import json
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import traceback

# Add migration to path
sys.path.append(str(Path(__file__).parent))

from data_base_strategy import DataBaseCalculator, DateBaseStrategy, CalculatedDates


@dataclass 
class EnrichmentMetadata:
    """Metadata sobre o processo de enriquecimento."""
    version: str = "v1.0"
    enriched_at: str = ""
    calculation_strategy: str = ""
    source_file: str = ""
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if not self.enriched_at:
            self.enriched_at = datetime.now().isoformat()


@dataclass
class CalculatedFields:
    """Campos calculados que serão adicionados ao JSON."""
    # Date fields calculated from duration
    planned_start_date: str = ""
    planned_end_date: str = ""
    calculated_duration_days: float = 0.0
    duration_unit: str = ""
    business_days_used: bool = False
    calculation_notes: str = ""
    
    # Task statistics (calculated from task array)
    total_tasks: int = 0
    tdd_tasks: int = 0
    analysis_tasks: int = 0
    estimated_total_minutes: int = 0
    estimated_total_hours: float = 0.0
    
    # Epic complexity metrics
    labels_count: int = 0
    goals_count: int = 0
    definition_of_done_count: int = 0
    
    # Task phase distribution
    task_phases: Dict[str, int] = None
    
    # Epic categorization
    epic_category: str = ""  # Based on labels
    complexity_score: int = 0  # 1-10 based on tasks, goals, etc.
    
    def __post_init__(self):
        if self.task_phases is None:
            self.task_phases = {}


class JSONEnrichmentEngine:
    """
    Engine para enriquecer JSONs de épicos com campos calculados.
    
    Mantém separação clara entre:
    - Dados originais (preservados)
    - Campos calculados (derivados)
    - Metadata (controle)
    """
    
    def __init__(self, base_strategy: DateBaseStrategy = DateBaseStrategy.NEXT_MONDAY):
        self.calculator = DataBaseCalculator(base_strategy)
        self.base_strategy = base_strategy
        
        # Epic categorization mapping
        self.category_mapping = {
            ('infra', 'deployment', 'production'): 'Infrastructure',
            ('security', 'audit', 'compliance'): 'Security', 
            ('performance', 'optimization'): 'Performance',
            ('tdd', 'testing', 'quality'): 'Quality',
            ('feature', 'enhancement'): 'Feature',
            ('bug', 'fix', 'maintenance'): 'Maintenance',
            ('docs', 'documentation'): 'Documentation'
        }
    
    def calculate_epic_dates(self, epic_data: Dict[str, Any]) -> CalculatedDates:
        """Calculate dates for epic using data base strategy."""
        try:
            return self.calculator.calculate_epic_dates(epic_data)
        except Exception as e:
            # Return empty dates if calculation fails
            return CalculatedDates(
                planned_start_date=date.today(),
                planned_end_date=date.today(),
                calculated_duration_days=0.0,
                duration_unit="dias",
                business_days_used=False,
                calculation_notes=f"Calculation failed: {str(e)}"
            )
    
    # TODO: Consider extracting this block into a separate method
    def analyze_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze task array and extract statistics."""
        if not tasks:
            return {
                'total_tasks': 0,
                'tdd_tasks': 0,
                'analysis_tasks': 0,
                'estimated_total_minutes': 0,
                'task_phases': {}
            }
        
        total_tasks = len(tasks)
        tdd_tasks = 0
        analysis_tasks = 0
        total_minutes = 0
        task_phases = {}
        
        for task in tasks:
            # Count TDD tasks (have tdd_phase field)
            if task.get('tdd_phase'):
                tdd_tasks += 1
                phase = task.get('tdd_phase', 'unknown')
                task_phases[phase] = task_phases.get(phase, 0) + 1
            
            # Count analysis tasks  
            if (task.get('tdd_skip_reason') == 'Analysis/documentation task' or
                'analysis' in task.get('title', '').lower()):
                analysis_tasks += 1
            
            # Sum estimated minutes
            minutes = task.get('estimate_minutes', 0)
            if isinstance(minutes, (int, float)):
                total_minutes += minutes
        
        return {
            'total_tasks': total_tasks,
            'tdd_tasks': tdd_tasks, 
            'analysis_tasks': analysis_tasks,
            'estimated_total_minutes': total_minutes,
            'estimated_total_hours': round(total_minutes / 60.0, 2),
            'task_phases': task_phases
        }
    
# TODO: Consider extracting this block into a separate method
    
    def categorize_epic(self, epic_data: Dict[str, Any]) -> Tuple[str, int]:
        """
        Categorize epic based on labels and calculate complexity score.
        
        Returns:
            Tuple of (category, complexity_score)
        """
        labels = epic_data.get('labels', [])
        
        # Find category
        category = 'General'
        for keywords, cat_name in self.category_mapping.items():
            if any(keyword in labels for keyword in keywords):
                category = cat_name
                break
        
        # Calculate complexity score (1-10)
        score = 1
        
        # Add points for different factors
        score += min(len(labels), 3)  # +1-3 for labels
        score += min(len(epic_data.get('goals', [])), 2)  # +0-2 for goals
        score += min(len(epic_data.get('definition_of_done', [])), 2)  # +0-2 for DoD
        score += min(len(epic_data.get('tasks', [])) // 5, 2)  # +0-2 for task count
        
# TODO: Consider extracting this block into a separate method
        
        return category, min(score, 10)
    
    def enrich_epic(self, epic_data: Dict[str, Any], source_file: str = "") -> Dict[str, Any]:
        """
        Enrich a single epic with calculated fields.
        
        Args:
            epic_data: Original epic data from JSON
            source_file: Source file path for metadata
            
        Returns:
            Enriched epic with calculated_fields and metadata
        """
        try:
            # Calculate dates from duration
            calculated_dates = self.calculate_epic_dates(epic_data)
            
            # Analyze tasks
            tasks_analysis = self.analyze_tasks(epic_data.get('tasks', []))
            
            # Categorize epic
            category, complexity = self.categorize_epic(epic_data)
            
            # Build calculated fields
            calculated_fields = CalculatedFields(
                planned_start_date=calculated_dates.planned_start_date.isoformat(),
                planned_end_date=calculated_dates.planned_end_date.isoformat(),
                calculated_duration_days=calculated_dates.calculated_duration_days,
                duration_unit=calculated_dates.duration_unit,
                business_days_used=calculated_dates.business_days_used,
                calculation_notes=calculated_dates.calculation_notes,
                
                total_tasks=tasks_analysis['total_tasks'],
                tdd_tasks=tasks_analysis['tdd_tasks'],
                analysis_tasks=tasks_analysis['analysis_tasks'],
                estimated_total_minutes=tasks_analysis['estimated_total_minutes'],
                estimated_total_hours=tasks_analysis['estimated_total_hours'],
                
                labels_count=len(epic_data.get('labels', [])),
                goals_count=len(epic_data.get('goals', [])),
                definition_of_done_count=len(epic_data.get('definition_of_done', [])),
                
                task_phases=tasks_analysis['task_phases'],
                epic_category=category,
                complexity_score=complexity
            )
            
            # Build metadata
            metadata = EnrichmentMetadata(
                version="v1.0",
                calculation_strategy=self.base_strategy.value,
                source_file=source_file
            )
            
            # Return enriched epic (original + calculated + metadata)
            enriched = {
                **epic_data,  # Original data preserved
                'calculated_fields': asdict(calculated_fields),
                'metadata': asdict(metadata)
            }
            
            return enriched
            
        except Exception as e:
            # Return original data with error metadata
            error_metadata = EnrichmentMetadata(
                source_file=source_file,
                errors=[f"Enrichment failed: {str(e)}"]
            )
            
            return {
                # TODO: Consider extracting this block into a separate method
                **epic_data,
                'calculated_fields': asdict(CalculatedFields()),
                'metadata': asdict(error_metadata)
            }
    
    def enrich_epic_file(self, file_path: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Enrich epic from JSON file.
        
        Args:
            file_path: Path to input JSON file
            output_path: Path to save enriched JSON (optional)
            
        Returns:
            Enriched epic data
        """
        try:
            # Load original JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                original_data = json.load(f)
            
            # Extract epic data (handle nested structure)
            if 'epic' in original_data:
                epic_data = original_data['epic'] 
                wrapper = original_data
            else:
                epic_data = original_data
                wrapper = None
            
            # Enrich epic
            enriched_epic = self.enrich_epic(epic_data, str(file_path))
            
            # Rebuild structure if was nested
            if wrapper:
                result = {
                    **wrapper,
                    'epic': enriched_epic
                }
            else:
                result = enriched_epic
            
            # Save if output path provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"✅ Enriched epic saved to {output_path}")
            
            return result
            
# TODO: Consider extracting this block into a separate method
            
        except Exception as e:
            print(f"❌ Error enriching {file_path}: {e}")
            traceback.print_exc()
            return {}
    
    def enrich_all_epics(self, epics_dir: Path, output_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Enrich all epic files in a directory.
        
        Args:
            epics_dir: Directory containing epic JSON files
            output_dir: Directory to save enriched files (optional)
            
        Returns:
            List of enriched epics
        """
        enriched_epics = []
        
        # Find all JSON files
        json_files = list(epics_dir.glob('*.json'))
        
        if not json_files:
            print(f"⚠️ No JSON files found in {epics_dir}")
            return []
        
        print(f"🔍 Found {len(json_files)} epic files to enrich")
        
        for file_path in json_files:
            print(f"📄 Processing {file_path.name}...")
            
            # Determine output path
            if output_dir:
                output_dir.mkdir(exist_ok=True)
                output_path = output_dir / f"enriched_{file_path.name}"
            else:
                output_path = None
            
            # Enrich epic
            enriched = self.enrich_epic_file(file_path, output_path)
            if enriched:
                enriched_epics.append(enriched)
        
        print(f"✅ Enriched {len(enriched_epics)} epics successfully")
        return enriched_epics


# TODO: Consider extracting this block into a separate method
def main():
    """Main function to test JSON enrichment."""
    print("✨ JSON Enrichment Engine Test")
    print("=" * 60)
    
    # Test with single epic
    epics_dir = Path("epics/user_epics")
    if not epics_dir.exists():
        print(f"❌ Directory {epics_dir} not found")
        return
    
    # Initialize engine
    engine = JSONEnrichmentEngine(DateBaseStrategy.NEXT_MONDAY)
    
    # Test with epico_0.json
    test_file = epics_dir / "epico_0.json"
    if test_file.exists():
        print(f"🧪 Testing with {test_file.name}")
        enriched = engine.enrich_epic_file(test_file)
        
        if enriched:
            # Show enrichment results
            if 'epic' in enriched:
                calc_fields = enriched['epic'].get('calculated_fields', {})
                metadata = enriched['epic'].get('metadata', {})
            else:
                calc_fields = enriched.get('calculated_fields', {})
                metadata = enriched.get('metadata', {})
            
            print("\\n📊 Enrichment Results:")
            print(f"   Planned Start: {calc_fields.get('planned_start_date')}")
            print(f"   Planned End: {calc_fields.get('planned_end_date')}")
            print(f"   Duration: {calc_fields.get('calculated_duration_days')} days")
            print(f"   Total Tasks: {calc_fields.get('total_tasks')}")
            print(f"   TDD Tasks: {calc_fields.get('tdd_tasks')}")
            print(f"   Category: {calc_fields.get('epic_category')}")
            print(f"   Complexity: {calc_fields.get('complexity_score')}/10")
            print(f"   Strategy: {metadata.get('calculation_strategy')}")
    
    # Test enriching all epics
    print("\\n🔄 Testing batch enrichment...")
    output_dir = Path("epics/enriched")
    enriched_epics = engine.enrich_all_epics(epics_dir, output_dir)
    
    print(f"\\n✅ JSON Enrichment Engine working correctly!")
    print(f"Enriched {len(enriched_epics)} epics total")


if __name__ == "__main__":
    main()