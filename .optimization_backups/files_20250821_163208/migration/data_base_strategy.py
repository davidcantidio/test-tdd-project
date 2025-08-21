#!/usr/bin/env python3
"""
📅 Data Base Strategy for Epic Duration Calculation

Sistema para converter duração textual ("2 dias") em datas planejadas
baseado em uma data base configurável.

Estratégia:
- Duração textual do JSON → planned_start_date + planned_end_date no banco
- Considera dias úteis vs calendário baseado no contexto do épico
- Data base configurável (ex: próxima segunda, data específica)
"""

from datetime import datetime, date, timedelta
from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re
import sys
from pathlib import Path

# Add duration_system to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from duration_system.duration_calculator import DurationCalculator
    from duration_system.business_calendar import get_global_calendar
    DURATION_SYSTEM_AVAILABLE = True
except ImportError:
    print("⚠️ Duration system not available, using basic implementation")
    DURATION_SYSTEM_AVAILABLE = False


class DateBaseStrategy(Enum):
    """Estratégias para definir data base de cálculo."""
    NEXT_MONDAY = "next_monday"           # Próxima segunda-feira
    SPECIFIC_DATE = "specific_date"       # Data específica fornecida
    TODAY = "today"                       # Hoje
    NEXT_BUSINESS_DAY = "next_business"   # Próximo dia útil


class DurationUnit(Enum):
    """Unidades de duração suportadas."""
    DAYS = "dias"
    WEEKS = "semanas"  
    HOURS = "horas"
    BUSINESS_DAYS = "dias_uteis"


@dataclass
class CalculatedDates:
    """Resultado do cálculo de datas baseado em duração."""
    planned_start_date: date
    planned_end_date: date
    calculated_duration_days: float
    duration_unit: str
    business_days_used: bool
    calculation_notes: str


class DataBaseCalculator:
    """
    Calculadora de datas baseada em duração textual e data base.
    
    Converte durações como "2 dias", "1 semana" em datas planejadas
    baseado em uma estratégia de data base configurável.
    """
    
    # TODO: Consider extracting this block into a separate method
    def __init__(self, base_strategy: DateBaseStrategy = DateBaseStrategy.NEXT_MONDAY,
                 specific_date: Optional[date] = None):
        self.base_strategy = base_strategy
        self.specific_date = specific_date
        self.duration_calculator = None
        
        # Initialize duration calculator if available
        if DURATION_SYSTEM_AVAILABLE:
            self.duration_calculator = DurationCalculator()
            self.business_calendar = get_global_calendar()
        
        # Regex patterns for duration parsing
        self.duration_patterns = {
            'dias': re.compile(r'(\d+\.?\d*)\s*dias?'),
            'semanas': re.compile(r'(\d+\.?\d*)\s*semanas?'),
            'horas': re.compile(r'(\d+\.?\d*)\s*horas?'),
        }
    
# TODO: Consider extracting this block into a separate method
    
    def get_base_date(self, reference_date: Optional[date] = None) -> date:
        """
        Calcula a data base baseada na estratégia configurada.
        
        Args:
            reference_date: Data de referência (default: hoje)
            
        Returns:
            Data base para início dos cálculos
        """
        if reference_date is None:
            reference_date = date.today()
        
        if self.base_strategy == DateBaseStrategy.TODAY:
            return reference_date
        
        elif self.base_strategy == DateBaseStrategy.SPECIFIC_DATE:
            if self.specific_date is None:
                raise ValueError("Specific date required for SPECIFIC_DATE strategy")
            return self.specific_date
        
        elif self.base_strategy == DateBaseStrategy.NEXT_MONDAY:
            # Find next Monday (or today if it's Monday)
            days_ahead = 0 - reference_date.weekday()  # Monday is 0
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return reference_date + timedelta(days_ahead)
        
        elif self.base_strategy == DateBaseStrategy.NEXT_BUSINESS_DAY:
            if DURATION_SYSTEM_AVAILABLE:
                return self.business_calendar.get_next_business_day(reference_date)
            else:
                # Simple implementation - skip weekends
                candidate = reference_date
                while candidate.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    candidate += timedelta(days=1)
                return candidate
        
        # TODO: Consider extracting this block into a separate method
        else:
            raise ValueError(f"Unknown base strategy: {self.base_strategy}")
    
    def parse_duration_string(self, duration_str: str) -> Tuple[float, str]:
        """
        Parse duration string into numeric value and unit.
        
        Args:
            duration_str: Duration like "2 dias", "1.5 semanas"
            
        Returns:
            Tuple of (numeric_value, unit)
            
        Examples:
            "2 dias" → (2.0, "dias")
            "1.5 semanas" → (1.5, "semanas")
        """
        duration_str = duration_str.lower().strip()
        
        for unit, pattern in self.duration_patterns.items():
            match = pattern.search(duration_str)
            if match:
                value = float(match.group(1))
                return value, unit
        
        # Fallback - try to extract number and assume days
        number_match = re.search(r'(\d+\.?\d*)', duration_str)
        if number_match:
            # TODO: Consider extracting this block into a separate method
            return float(number_match.group(1)), 'dias'
        
        raise ValueError(f"Could not parse duration string: {duration_str}")
    
    def calculate_end_date(self, start_date: date, duration_value: float, 
                          duration_unit: str, use_business_days: bool = False) -> date:
        """
        Calculate end date based on start date, duration value and unit.
        
        Args:
            start_date: Starting date
            duration_value: Numeric duration (e.g., 2.0)
            duration_unit: Unit of duration ("dias", "semanas", "horas")
            use_business_days: Whether to use business days calculation
            
        Returns:
            Calculated end date
        """
        if duration_unit == 'horas':
            # For hours, assume 8 hours = 1 day
            duration_days = duration_value / 8.0
        elif duration_unit == 'semanas':
            duration_days = duration_value * 7.0
        else:  # 'dias' or default
            duration_days = duration_value
        
        if use_business_days and DURATION_SYSTEM_AVAILABLE:
            # TODO: Consider extracting this block into a separate method
            return self.business_calendar.add_business_days(start_date, int(duration_days))
        else:
            # Calendar days calculation
            return start_date + timedelta(days=int(duration_days))
    
    def should_use_business_days(self, epic_data: Dict[str, Any]) -> bool:
        """
        Determine if business days should be used based on epic context.
        
        Args:
            epic_data: Epic data from JSON
            
        Returns:
            True if business days should be used
        """
        # Check labels for business context indicators
        labels = epic_data.get('labels', [])
        business_labels = ['infra', 'deployment', 'production', 'business']
        
        if any(label in business_labels for label in labels):
            return True
        
        # Check if duration is long enough to warrant business days
        duration_str = epic_data.get('duration', '')
        try:
            duration_value, unit = self.parse_duration_string(duration_str)
            if unit == 'semanas' or (unit == 'dias' and duration_value >= 5):
                # TODO: Consider extracting this block into a separate method
                return True
        except ValueError:
            pass
        
        return False
    
    def calculate_epic_dates(self, epic_data: Dict[str, Any], 
                           reference_date: Optional[date] = None) -> CalculatedDates:
        """
        Calculate planned dates for an epic based on its duration.
        
        Args:
            epic_data: Epic data from JSON (must have 'duration' field)
            reference_date: Reference date for base calculation
            
        Returns:
            CalculatedDates object with all calculated information
        """
        duration_str = epic_data.get('duration', '')
        if not duration_str:
            raise ValueError("Epic data must contain 'duration' field")
        
        # Parse duration
        duration_value, duration_unit = self.parse_duration_string(duration_str)
        
        # Determine if business days should be used
        use_business_days = self.should_use_business_days(epic_data)
        
        # Calculate base date
        start_date = self.get_base_date(reference_date)
        
        # Calculate end date
        end_date = self.calculate_end_date(start_date, duration_value, 
                                         duration_unit, use_business_days)
        
        # Calculate actual duration in days (calendar days)
        actual_duration_days = (end_date - start_date).days
        
        # Generate calculation notes
        base_strategy_desc = {
            DateBaseStrategy.NEXT_MONDAY: "próxima segunda-feira",
            DateBaseStrategy.SPECIFIC_DATE: f"data específica ({self.specific_date})",
            DateBaseStrategy.TODAY: "hoje",
            DateBaseStrategy.NEXT_BUSINESS_DAY: "próximo dia útil"
        }
        
        notes = (
            f"Duração '{duration_str}' ({duration_value} {duration_unit}) "
            f"a partir de {base_strategy_desc[self.base_strategy]} ({start_date}). "
            f"Dias {'úteis' if use_business_days else 'calendário'} utilizados."
        )
        
        return CalculatedDates(
            planned_start_date=start_date,
            planned_end_date=end_date,
            calculated_duration_days=actual_duration_days,
            duration_unit=duration_unit,
            business_days_used=use_business_days,
            calculation_notes=notes
        )


# TODO: Consider extracting this block into a separate method
def validate_with_example():
    """Validate the data base strategy with example epic."""
    print("🧪 Validating Data Base Strategy with Example Epic")
    print("=" * 60)
    
    # Example epic data (similar to epico_0.json)
    example_epic = {
        "duration": "2 dias",
        "labels": ["infra", "compatibility", "performance", "env", "safety"],
        "name": "Environment & Production Safety"
    }
    
    print(f"Example Epic: {example_epic['name']}")
    print(f"Duration: {example_epic['duration']}")
    print(f"Labels: {example_epic['labels']}")
    print()
    
    # Test different strategies
    strategies = [
        (DateBaseStrategy.TODAY, None),
        (DateBaseStrategy.NEXT_MONDAY, None),
        (DateBaseStrategy.SPECIFIC_DATE, date(2025, 8, 18)),  # Next Monday
        (DateBaseStrategy.NEXT_BUSINESS_DAY, None)
    ]
    
    for strategy, specific_date in strategies:
        print(f"📅 Strategy: {strategy.value}")
        
        try:
            calculator = DataBaseCalculator(strategy, specific_date)
            result = calculator.calculate_epic_dates(example_epic)
            
            print(f"   Start Date: {result.planned_start_date}")
            print(f"   End Date: {result.planned_end_date}")
            print(f"   Duration: {result.calculated_duration_days} days")
            print(f"   Business Days Used: {result.business_days_used}")
            print(f"   Notes: {result.calculation_notes}")
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()


# TODO: Consider extracting this block into a separate method

def create_default_config() -> Dict[str, Any]:
    """Create default configuration for data base strategy."""
    return {
        "default_strategy": "next_monday",
        "epic_specific_dates": {
            # Can override specific epics if needed
            # "epic_0": "2025-08-18",
        },
        "business_day_labels": ["infra", "deployment", "production", "business"],
        "long_duration_threshold": {
            "dias": 5,
            "semanas": 1
        },
        "reference_date": None  # Use today if None
    }


if __name__ == "__main__":
    # Run validation
    validate_with_example()
    
    # Show default config
    print("📋 Default Configuration")
    print("=" * 60)
    config = create_default_config()
    for key, value in config.items():
        print(f"{key}: {value}")