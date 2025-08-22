#!/usr/bin/env python3
"""
🎨 TDD Project Template - Diagram Generator

Generates Mermaid diagrams from epic JSON files:
- Mindmap: Hierarchical project structure
- Flowchart: Epic dependencies and workflow
- Gantt: Professional timeline with GitHub integration

Usage:
    python3 generate_all_diagrams.py [--github-repo REPO] [--output-dir DIR]
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sys

def load_epic_files(epic_dir: Path = Path("epics")) -> List[Dict[str, Any]]:
    """Load and validate all epic JSON files."""
    epics = []
    
    if not epic_dir.exists():
        print(f"⚠️ Epic directory not found: {epic_dir}")
        return epics
    
    epic_files = list(epic_dir.glob("*.json"))
    
    if not epic_files:
        print(f"⚠️ No epic JSON files found in {epic_dir}")
        return epics
    
    for epic_file in epic_files:
        try:
            with open(epic_file, 'r', encoding='utf-8') as f:
                epic_data = json.load(f)
                if 'epic' in epic_data:
                    epics.append(epic_data['epic'])
                    print(f"✅ Loaded epic: {epic_data['epic'].get('name', epic_file.name)}")
                else:
                    print(f"⚠️ Invalid epic format: {epic_file.name}")
        except Exception as e:
            print(f"❌ Error loading {epic_file.name}: {e}")
    
    return epics

def generate_mindmap(epics: List[Dict[str, Any]]) -> str:
    """Generate Mermaid mindmap from epics."""
    mindmap = "mindmap\n  root((TDD Project))\n"
    
    for epic in epics:
        epic_id = epic.get('id', 'EPIC-?')
        epic_name = epic.get('name', 'Unnamed Epic')
        mindmap += f"    {epic_id}\n"
        mindmap += f"      [{epic_name}]\n"
        
        tasks = epic.get('tasks', [])
        for task in tasks:
            task_id = task.get('id', 'TASK-?')
            task_title = task.get('title', 'Unnamed Task')
            tdd_phase = task.get('tdd_phase', 'unknown')
            phase_icon = {
                'red': '🔴',
                'green': '🟢', 
                'refactor': '🔄'
            }.get(tdd_phase, '⚪')
            
            mindmap += f"        {task_id}\n"
            mindmap += f"          {phase_icon} {task_title}\n"
    
    return mindmap

def generate_flowchart(epics: List[Dict[str, Any]]) -> str:
    """Generate Mermaid flowchart showing epic dependencies."""
    flowchart = "flowchart TD\n"
    flowchart += "    Start([Project Start])\n"
    
    # Add epic nodes
    for epic in epics:
        epic_id = epic.get('id', 'EPIC-?').replace('-', '_')
        epic_name = epic.get('name', 'Unnamed Epic')
        flowchart += f"    {epic_id}[{epic_name}]\n"
        flowchart += f"    Start --> {epic_id}\n"
    
    # Add task nodes and dependencies
    for epic in epics:
        epic_id = epic.get('id', 'EPIC-?').replace('-', '_')
        tasks = epic.get('tasks', [])
        
        for task in tasks:
            task_id = task.get('id', 'TASK-?').replace('-', '_').replace('.', '_')
            task_title = task.get('title', 'Unnamed Task')
            tdd_phase = task.get('tdd_phase', 'unknown')
            
            # Color coding by TDD phase
            phase_style = {
                'red': ':::red',
                'green': ':::green',
                'refactor': ':::blue'
            }.get(tdd_phase, '')
            
            flowchart += f"    {task_id}[{task_title}]{phase_style}\n"
            flowchart += f"    {epic_id} --> {task_id}\n"
            
            # Add dependencies
            dependencies = task.get('dependencies', [])
            for dep in dependencies:
                dep_id = dep.replace('-', '_').replace('.', '_')
                flowchart += f"    {dep_id} --> {task_id}\n"
    
    # Add styling
    flowchart += "\n    classDef red fill:#ffebee,stroke:#f44336,stroke-width:2px\n"
    flowchart += "    classDef green fill:#e8f5e8,stroke:#4caf50,stroke-width:2px\n"
    flowchart += "    classDef blue fill:#e3f2fd,stroke:#2196f3,stroke-width:2px\n"
    
    return flowchart

def generate_gantt(epics: List[Dict[str, Any]], github_repo: Optional[str] = None) -> str:
    """Generate professional Gantt chart with GitHub integration."""
    gantt = "gantt\n"
    gantt += "    title Professional TDD Project Timeline\n"
    gantt += "    dateFormat YYYY-MM-DD\n"
    gantt += "    axisFormat %d/%m\n"
    gantt += "    weekday monday\n\n"
    
    # Calculate start date (today)
    start_date = datetime.now()
    current_date = start_date
    
    for epic in epics:
        epic_name = epic.get('name', 'Unnamed Epic')
        epic_id = epic.get('id', 'EPIC-?')
        
        gantt += f"    section {epic_name}\n"
        
        tasks = epic.get('tasks', [])
        for i, task in enumerate(tasks):
            task_id = task.get('id', f'{epic_id}.{i+1}')
            task_title = task.get('title', 'Unnamed Task')
            tdd_phase = task.get('tdd_phase', 'unknown')
            estimate_minutes = task.get('estimate_minutes', 60)
            
            # Convert minutes to days (assuming 8h work day)
            task_duration = max(1, estimate_minutes // 480)  # 480 min = 8 hours
            
            # Phase styling
            phase_style = {
                'red': 'crit, ',
                'green': 'active, ',
                'refactor': 'done, '
            }.get(tdd_phase, '')
            
            task_end = current_date + timedelta(days=task_duration)
            
            # GitHub issue link if repo provided
            issue_link = ""
            if github_repo:
                issue_link = f" :#{task_id.replace('.', '_')}"
            
            gantt += f"    {task_title}{issue_link} :{phase_style}{task_id.lower().replace('.', '_')}, {current_date.strftime('%Y-%m-%d')}, {task_duration}d\n"
            
            current_date = task_end
            
            # Add weekend buffer
            if current_date.weekday() >= 5:  # Saturday or Sunday
                current_date += timedelta(days=7 - current_date.weekday())
    
    # Add milestone markers
    gantt += f"\n    milestone Project Start :milestone, m1, {start_date.strftime('%Y-%m-%d')}, 0d\n"
    gantt += f"    milestone Project End :milestone, m2, {current_date.strftime('%Y-%m-%d')}, 0d\n"
    
    return gantt

def save_diagrams(diagrams: Dict[str, str], output_dir: Path = Path("docs")):
    """Save generated diagrams to .mmd files."""
    output_dir.mkdir(exist_ok=True)
    
    for diagram_type, content in diagrams.items():
        output_file = output_dir / f"{diagram_type}.mmd"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📄 Generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate TDD project diagrams")
    parser.add_argument("--github-repo", help="GitHub repository (owner/repo)")
    parser.add_argument("--output-dir", default="docs", help="Output directory")
    args = parser.parse_args()
    
    print("🎨 TDD Diagram Generator Starting...")
    
    # Load epic files
    epics = load_epic_files()
    if not epics:
        print("❌ No epics found. Creating example epic...")
        # Create a simple example epic for demonstration
        example_epic = {
            "id": "EPIC-1",
            "name": "Project Setup",
            "tasks": [
                {
                    "id": "EPIC-1.1",
                    "title": "Initialize project structure",
                    "tdd_phase": "green",
                    "estimate_minutes": 120
                },
                {
                    "id": "EPIC-1.2", 
                    "title": "Setup testing framework",
                    "tdd_phase": "red",
                    "estimate_minutes": 90
                }
            ]
        }
        epics = [example_epic]
    
    # Generate diagrams
    diagrams = {
        "mindmap": generate_mindmap(epics),
        "flow_dependencies": generate_flowchart(epics),
        "gantt_schedule": generate_gantt(epics, args.github_repo)
    }
    
    # Save diagrams
    output_path = Path(args.output_dir)
    save_diagrams(diagrams, output_path)
    
    print(f"✅ Generated {len(diagrams)} diagrams in {output_path}")
    print("🌐 View diagrams at: https://mermaid.live/")

if __name__ == "__main__":
    main()