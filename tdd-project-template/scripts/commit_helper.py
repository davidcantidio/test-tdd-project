#!/usr/bin/env python3
"""
🧪 TDD Project Template - Commit Helper
======================================

Script para facilitar commits seguindo o padrão TDD:
[EPIC-X] phase: type: description [Task X.Y | Zmin]

Fases TDD:
- analysis: Análise de requisitos e planejamento
- red: Escrevendo testes que falham
- green: Implementação para fazer testes passarem
- refactor: Melhorias e limpeza do código

Uso:
    python scripts/commit_helper.py
    python scripts/commit_helper.py --interactive
    python scripts/commit_helper.py --quick --epic 1 --phase red --type feat --desc "Add user authentication" --task 1.2 --time 45
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List


class TDDCommitHelper:
    """Helper para gerar commits seguindo padrão TDD."""
    
    def __init__(self):
        self.tdd_phases = {
            'analysis': {
                'emoji': '🧪',
                'description': 'Requirements analysis and task planning',
                'common_types': ['docs', 'chore', 'feat']
            },
            'red': {
                'emoji': '🔴', 
                'description': 'Write failing tests first',
                'common_types': ['test', 'feat']
            },
            'green': {
                'emoji': '🟢',
                'description': 'Implement code to make tests pass', 
                'common_types': ['feat', 'fix', 'refactor']
            },
            'refactor': {
                'emoji': '🔄',
                'description': 'Clean and optimize code',
                'common_types': ['refactor', 'style', 'perf']
            }
        }
        
        self.commit_types = {
            'feat': 'New feature',
            'fix': 'Bug fix', 
            'docs': 'Documentation changes',
            'style': 'Code style changes (formatting, etc)',
            'refactor': 'Code refactoring',
            'test': 'Adding or updating tests',
            'chore': 'Maintenance tasks',
            'perf': 'Performance improvements',
            'build': 'Build system changes',
            'ci': 'CI/CD changes'
        }
    
    def validate_epic_exists(self, epic_id: str) -> bool:
        """Verificar se o épico existe nos arquivos JSON."""
        epic_files = [
            Path(f"epics/epic_{epic_id}.json"),
            Path(f"epicos/epico_{epic_id}.json")
        ]
        
        return any(f.exists() for f in epic_files)
    
    def get_current_tdd_phase(self, epic_id: str) -> Optional[str]:
        """Determinar fase TDD atual baseada no último commit do épico."""
        try:
            cmd = f'git log --oneline --grep="\\\\[EPIC-{epic_id}\\\\]" -n 1'
            last_commit = subprocess.check_output(cmd, shell=True, text=True).strip()
            
            if not last_commit:
                return 'analysis'  # Primeiro commit do épico
            
            # Parse TDD phase from last commit
            pattern = r'\[EPIC-\d+\.?\d*\]\s+(analysis|red|green|refactor):'
            match = re.search(pattern, last_commit)
            
            if match:
                last_phase = match.group(1)
                # Suggest next logical phase
                phase_order = ['analysis', 'red', 'green', 'refactor']
                try:
                    current_idx = phase_order.index(last_phase)
                    if current_idx < len(phase_order) - 1:
                        return phase_order[current_idx + 1]
                    else:
                        return 'refactor'  # Stay in refactor or start new cycle
                except ValueError:
                    return 'analysis'
            
            return 'analysis'
            
        except subprocess.CalledProcessError:
            return 'analysis'  # No commits yet
    
    def suggest_next_phase(self, current_phase: str) -> str:
        """Sugerir próxima fase TDD lógica."""
        phase_flow = {
            'analysis': 'red',
            'red': 'green', 
            'green': 'refactor',
            'refactor': 'red'  # Start new cycle or continue refactoring
        }
        return phase_flow.get(current_phase, 'analysis')
    
    def interactive_commit_builder(self) -> str:
        """Construir commit interativamente."""
        print("🧪 TDD Commit Helper - Interactive Mode")
        print("=" * 50)
        
        # Epic selection
        epic_id = input("📋 Epic ID (e.g., 1, 2.5): ").strip()
        if not epic_id:
            print("❌ Epic ID is required!")
            return ""
        
        # Validate epic exists
        if not self.validate_epic_exists(epic_id):
            print(f"⚠️ Warning: Epic {epic_id} not found in epics/ directory")
            if input("Continue anyway? (y/N): ").lower() != 'y':
                return ""
        
        # Suggest current TDD phase
        suggested_phase = self.get_current_tdd_phase(epic_id)
        print(f"\n🧪 TDD Phases (suggested: {suggested_phase}):")
        for phase, info in self.tdd_phases.items():
            marker = " ← suggested" if phase == suggested_phase else ""
            print(f"  {info['emoji']} {phase}: {info['description']}{marker}")
        
        phase = input(f"TDD Phase [{suggested_phase}]: ").strip() or suggested_phase
        if phase not in self.tdd_phases:
            print(f"❌ Invalid phase! Must be one of: {', '.join(self.tdd_phases.keys())}")
            return ""
        
        # Commit type selection
        print(f"\n📝 Common types for {phase} phase:")
        common_types = self.tdd_phases[phase]['common_types']
        for t in common_types:
            print(f"  • {t}: {self.commit_types[t]}")
        
        commit_type = input(f"Commit type [{common_types[0]}]: ").strip() or common_types[0]
        if commit_type not in self.commit_types:
            print(f"❌ Invalid type! Must be one of: {', '.join(self.commit_types.keys())}")
            return ""
        
        # Description
        description = input("📄 Description: ").strip()
        if not description:
            print("❌ Description is required!")
            return ""
        
        # Task info (optional)
        print("\n🏷️ Task Information (optional):")
        task_id = input("Task ID (e.g., 1.2): ").strip()
        time_minutes = ""
        
        if task_id:
            time_minutes = input("Time spent (minutes): ").strip()
            if time_minutes and not time_minutes.isdigit():
                print("❌ Time must be a number!")
                return ""
        
        # Build commit message
        return self.build_commit_message(epic_id, phase, commit_type, description, task_id, time_minutes)
    
    def build_commit_message(self, epic_id: str, phase: str, commit_type: str, 
                           description: str, task_id: str = "", time_minutes: str = "") -> str:
        """Construir mensagem de commit no padrão TDD."""
        
        # Base message: [EPIC-X] phase: type: description
        base_msg = f"[EPIC-{epic_id}] {phase}: {commit_type}: {description}"
        
        # Add task info if provided
        if task_id and time_minutes:
            base_msg += f" [Task {task_id} | {time_minutes}min]"
        elif task_id:
            base_msg += f" [Task {task_id}]"
        
        return base_msg
    
    def validate_commit_message(self, message: str) -> Tuple[bool, List[str]]:
        """Validar mensagem de commit contra padrão TDD."""
        
        errors = []
        
        # Check TDD pattern
        tdd_pattern = r'\[EPIC-(\d+\.?\d*)\]\s+(analysis|red|green|refactor):\s+(\w+):\s+(.+?)(?:\s*\[Task\s+([\w.-]+)(?:\s*\|\s*(\d+)min)?\])?$'
        
        if not re.match(tdd_pattern, message):
            errors.append("Message doesn't match TDD pattern: [EPIC-X] phase: type: description [Task X.Y | Zmin]")
            return False, errors
        
        match = re.match(tdd_pattern, message)
        epic_id, phase, commit_type, description, task_id, time_minutes = match.groups()
        
        # Validate phase
        if phase not in self.tdd_phases:
            errors.append(f"Invalid TDD phase '{phase}'. Must be: {', '.join(self.tdd_phases.keys())}")
        
        # Validate type
        if commit_type not in self.commit_types:
            errors.append(f"Invalid commit type '{commit_type}'. Must be: {', '.join(self.commit_types.keys())}")
        
        # Validate description
        if len(description.strip()) < 5:
            errors.append("Description too short (minimum 5 characters)")
        
        if len(description) > 100:
            errors.append("Description too long (maximum 100 characters)")
        
        return len(errors) == 0, errors
    
    def execute_commit(self, message: str, auto_stage: bool = True) -> bool:
        """Executar o commit com a mensagem."""
        
        try:
            if auto_stage:
                # Stage all changes
                subprocess.run(['git', 'add', '.'], check=True)
                print("📁 Staged all changes")
            
            # Create commit
            subprocess.run(['git', 'commit', '-m', message], check=True)
            print("✅ Commit created successfully!")
            
            # Show commit info
            subprocess.run(['git', 'log', '-1', '--oneline'], check=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git command failed: {e}")
            return False
    
    def show_tdd_guide(self):
        """Mostrar guia rápido TDD."""
        print("\n🧪 TDD Workflow Guide")
        print("=" * 30)
        print("1. 🧪 Analysis: Plan and analyze requirements")
        print("   Example: [EPIC-1] analysis: docs: add user story for login [Task 1.1 | 15min]")
        print()
        print("2. 🔴 Red: Write failing tests first")
        print("   Example: [EPIC-1] red: test: add login validation test [Task 1.2 | 30min]")
        print()
        print("3. 🟢 Green: Implement code to make tests pass")
        print("   Example: [EPIC-1] green: feat: implement login validation [Task 1.3 | 45min]")
        print()
        print("4. 🔄 Refactor: Clean and optimize code")
        print("   Example: [EPIC-1] refactor: refactor: extract validation utility [Task 1.4 | 20min]")
        print()
        print("💡 Tips:")
        print("  • Always start with analysis for new epics")
        print("  • Follow red → green → refactor cycle")
        print("  • Keep commits small and focused")
        print("  • Include time estimates for better tracking")


def main():
    parser = argparse.ArgumentParser(
        description="🧪 TDD Project Template - Commit Helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/commit_helper.py                                    # Interactive mode
  python scripts/commit_helper.py --guide                           # Show TDD guide
  
  # Quick commit
  python scripts/commit_helper.py --quick \\
    --epic 1 --phase red --type test \\
    --desc "Add user authentication tests" \\
    --task 1.2 --time 30
    
  # Validate commit message  
  python scripts/commit_helper.py --validate "[EPIC-1] red: test: add login test [Task 1.1 | 30min]"
        """
    )
    
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive commit builder (default)')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='Quick commit mode with parameters')
    parser.add_argument('--guide', '-g', action='store_true',
                       help='Show TDD workflow guide')
    parser.add_argument('--validate', '-v', type=str,
                       help='Validate commit message format')
    
    # Quick mode parameters
    parser.add_argument('--epic', type=str, help='Epic ID')
    parser.add_argument('--phase', type=str, choices=['analysis', 'red', 'green', 'refactor'],
                       help='TDD phase')
    parser.add_argument('--type', type=str, help='Commit type')
    parser.add_argument('--desc', type=str, help='Commit description')
    parser.add_argument('--task', type=str, help='Task ID')
    parser.add_argument('--time', type=str, help='Time spent in minutes')
    
    parser.add_argument('--no-commit', action='store_true',
                       help='Only generate message, do not commit')
    parser.add_argument('--no-stage', action='store_true', 
                       help='Do not auto-stage files')
    
    args = parser.parse_args()
    
    helper = TDDCommitHelper()
    
    # Show TDD guide
    if args.guide:
        helper.show_tdd_guide()
        return 0
    
    # Validate commit message
    if args.validate:
        is_valid, errors = helper.validate_commit_message(args.validate)
        if is_valid:
            print("✅ Valid TDD commit message!")
        else:
            print("❌ Invalid commit message:")
            for error in errors:
                print(f"  • {error}")
        return 0 if is_valid else 1
    
    # Quick mode
    if args.quick:
        if not all([args.epic, args.phase, args.type, args.desc]):
            print("❌ Quick mode requires --epic, --phase, --type, and --desc")
            return 1
        
        message = helper.build_commit_message(
            args.epic, args.phase, args.type, args.desc,
            args.task or "", args.time or ""
        )
    else:
        # Interactive mode (default)
        message = helper.interactive_commit_builder()
    
    if not message:
        print("❌ No commit message generated")
        return 1
    
    # Validate generated message
    is_valid, errors = helper.validate_commit_message(message)
    if not is_valid:
        print("❌ Generated message is invalid:")
        for error in errors:
            print(f"  • {error}")
        return 1
    
    print(f"\n📝 Generated commit message:")
    print(f"   {message}")
    
    if args.no_commit:
        print("\n💡 Use: git commit -m \"<message>\"")
        return 0
    
    # Confirm and execute commit
    if not args.quick:
        if input("\n🤔 Create this commit? (Y/n): ").lower() in ('n', 'no'):
            print("❌ Commit cancelled")
            return 1
    
    success = helper.execute_commit(message, not args.no_stage)
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        exit(1)