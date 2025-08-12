#!/usr/bin/env python3
"""
📊 TDD Project - Enhanced Gantt Progress Tracker

Generates interactive HTML progress dashboard with:
- Real-time TDD phase tracking
- Commit pattern analysis
- Progress analytics
- Interactive Plotly charts

Usage:
    python3 gantt_tracker.py [--output OUTPUT] [--no-open]
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import subprocess
import sys
import re

# Graceful import handling
try:
    import plotly.graph_objects as go
    import plotly.express as px
    import plotly.figure_factory as ff
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

def load_epic_files() -> List[Dict[str, Any]]:
    """Load epic JSON files from epics directory."""
    epics = []
    epic_dir = Path("epics")
    
    if not epic_dir.exists():
        return epics
    
    for epic_file in epic_dir.glob("*.json"):
        try:
            with open(epic_file, 'r', encoding='utf-8') as f:
                epic_data = json.load(f)
                # Handle different epic JSON structures
                if 'epic' in epic_data:
                    epics.append(epic_data['epic'])
                elif 'epic_id' in epic_data or 'title' in epic_data:
                    # Handle flat structure (like epic_1.json)
                    epics.append(epic_data)
                else:
                    print(f"⚠️ Unrecognized epic format in {epic_file}")
        except Exception as e:
            print(f"⚠️ Error loading {epic_file}: {e}")
    
    return epics

def analyze_git_commits() -> Dict[str, Any]:
    """Analyze git commits for TDD patterns."""
    try:
        # Get recent commits
        result = subprocess.run([
            'git', 'log', '--oneline', '--since=30 days ago'
        ], capture_output=True, text=True, check=True)
        
        commits = result.stdout.strip().split('\n')
        
        # Analyze TDD patterns
        tdd_patterns = {
            'red': len([c for c in commits if re.search(r'(red:|test:|failing)', c.lower())]),
            'green': len([c for c in commits if re.search(r'(green:|impl:|implement)', c.lower())]),
            'refactor': len([c for c in commits if re.search(r'(refactor:|clean:|optimize)', c.lower())]),
            'epic': len([c for c in commits if re.search(r'\[EPIC-\d+\]', c)])
        }
        
        return {
            'total_commits': len([c for c in commits if c.strip()]),
            'tdd_commits': tdd_patterns,
            'last_commit': commits[0] if commits and commits[0].strip() else "No commits",
            'analysis_date': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"⚠️ Git analysis failed: {e}")
        return {
            'total_commits': 0,
            'tdd_commits': {'red': 0, 'green': 0, 'refactor': 0, 'epic': 0},
            'last_commit': "Analysis unavailable",
            'analysis_date': datetime.now().isoformat()
        }

def calculate_epic_progress(epics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate progress for each epic."""
    progress_data = []
    
    for epic in epics:
        tasks = epic.get('tasks', [])
        total_tasks = len(tasks)
        
        if total_tasks == 0:
            continue
        
        # Count completed phases
        phase_counts = {'red': 0, 'green': 0, 'refactor': 0}
        total_estimate = 0
        
        for task in tasks:
            phase = task.get('tdd_phase', 'unknown')
            if phase in phase_counts:
                phase_counts[phase] += 1
            
            estimate = task.get('estimate_minutes', 60)
            total_estimate += estimate
        
        # Calculate completion percentage
        completed_tasks = phase_counts['green'] + phase_counts['refactor']
        completion_percentage = (completed_tasks / total_tasks) * 100
        
        progress_data.append({
            'epic_id': epic.get('id', 'Unknown'),
            'epic_name': epic.get('name', 'Unnamed Epic'),
            'total_tasks': total_tasks,
            'phase_distribution': phase_counts,
            'completion_percentage': completion_percentage,
            'total_estimate_hours': total_estimate / 60,
            'duration_days': epic.get('duration', 'Unknown')
        })
    
    return progress_data

def generate_fallback_html(epics: List[Dict[str, Any]], git_analysis: Dict[str, Any], 
                          progress_data: List[Dict[str, Any]]) -> str:
    """Generate fallback HTML when Plotly is not available."""
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>TDD Progress Tracker - Fallback Mode</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            background: #f5f5f5;
        }
        .container { 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .metric-card { 
            display: inline-block; 
            margin: 10px; 
            padding: 20px; 
            border-radius: 8px; 
            min-width: 150px;
            text-align: center;
        }
        .red-phase { background: #ffebee; border-left: 4px solid #f44336; }
        .green-phase { background: #e8f5e8; border-left: 4px solid #4caf50; }
        .refactor-phase { background: #e3f2fd; border-left: 4px solid #2196f3; }
        .epic-card { 
            margin: 20px 0; 
            padding: 15px; 
            border: 1px solid #ddd; 
            border-radius: 8px;
        }
        .progress-bar { 
            background: #f0f0f0; 
            border-radius: 10px; 
            height: 20px; 
            overflow: hidden;
        }
        .progress-fill { 
            background: #4caf50; 
            height: 100%; 
            transition: width 0.3s;
        }
        h1 { color: #333; text-align: center; }
        h2 { color: #555; border-bottom: 2px solid #eee; padding-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 TDD Progress Tracker</h1>
        <p><em>Fallback mode - Install plotly for interactive charts</em></p>
        
        <h2>📊 Project Overview</h2>
"""
    
    # Add epic progress
    for epic in progress_data:
        html += f"""
        <div class="epic-card">
            <h3>{epic['epic_id']}: {epic['epic_name']}</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {epic['completion_percentage']:.1f}%"></div>
            </div>
            <p>Progress: {epic['completion_percentage']:.1f}% ({epic['total_tasks']} tasks)</p>
            <p>Estimate: {epic['total_estimate_hours']:.1f} hours</p>
        </div>
        """
    
    # Add TDD phase distribution
    total_red = sum(e['phase_distribution']['red'] for e in progress_data)
    total_green = sum(e['phase_distribution']['green'] for e in progress_data)
    total_refactor = sum(e['phase_distribution']['refactor'] for e in progress_data)
    
    html += f"""
        <h2>🧪 TDD Phase Distribution</h2>
        <div class="metric-card red-phase">
            <h3>🔴 RED</h3>
            <p>{total_red} tasks</p>
        </div>
        <div class="metric-card green-phase">
            <h3>🟢 GREEN</h3>
            <p>{total_green} tasks</p>
        </div>
        <div class="metric-card refactor-phase">
            <h3>🔄 REFACTOR</h3>
            <p>{total_refactor} tasks</p>
        </div>
        
        <h2>📈 Git Analysis</h2>
        <p><strong>Total Commits (30 days):</strong> {git_analysis['total_commits']}</p>
        <p><strong>TDD Pattern Commits:</strong></p>
        <ul>
            <li>RED phase: {git_analysis['tdd_commits']['red']}</li>
            <li>GREEN phase: {git_analysis['tdd_commits']['green']}</li>
            <li>REFACTOR phase: {git_analysis['tdd_commits']['refactor']}</li>
            <li>Epic commits: {git_analysis['tdd_commits']['epic']}</li>
        </ul>
        <p><strong>Last Commit:</strong> {git_analysis['last_commit']}</p>
        
        <hr>
        <p><small>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
        <p><small>🤖 TDD Project Template - Enhanced Progress Tracker</small></p>
    </div>
</body>
</html>
    """
    
    return html

def generate_interactive_html(epics: List[Dict[str, Any]], git_analysis: Dict[str, Any], 
                            progress_data: List[Dict[str, Any]]) -> str:
    """Generate interactive Plotly dashboard."""
    if not PLOTLY_AVAILABLE:
        return generate_fallback_html(epics, git_analysis, progress_data)
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Epic Progress', 'TDD Phase Distribution', 'Commit Patterns', 'Time Estimates'],
        specs=[[{'type': 'bar'}, {'type': 'pie'}],
               [{'type': 'bar'}, {'type': 'scatter'}]]
    )
    
    # Epic Progress Chart
    epic_names = [e['epic_name'] for e in progress_data]
    completion_percentages = [e['completion_percentage'] for e in progress_data]
    
    fig.add_trace(
        go.Bar(
            x=epic_names,
            y=completion_percentages,
            name='Completion %',
            marker_color=['#4caf50' if p >= 50 else '#ff9800' for p in completion_percentages]
        ),
        row=1, col=1
    )
    
    # TDD Phase Distribution
    total_red = sum(e['phase_distribution']['red'] for e in progress_data)
    total_green = sum(e['phase_distribution']['green'] for e in progress_data) 
    total_refactor = sum(e['phase_distribution']['refactor'] for e in progress_data)
    
    fig.add_trace(
        go.Pie(
            labels=['RED', 'GREEN', 'REFACTOR'],
            values=[total_red, total_green, total_refactor],
            marker_colors=['#f44336', '#4caf50', '#2196f3'],
            name='TDD Phases'
        ),
        row=1, col=2
    )
    
    # Commit Patterns
    commit_types = list(git_analysis['tdd_commits'].keys())
    commit_counts = list(git_analysis['tdd_commits'].values())
    
    fig.add_trace(
        go.Bar(
            x=commit_types,
            y=commit_counts,
            name='Commit Types',
            marker_color=['#f44336', '#4caf50', '#2196f3', '#ff9800']
        ),
        row=2, col=1
    )
    
    # Time Estimates vs Tasks
    task_counts = [e['total_tasks'] for e in progress_data]
    time_estimates = [e['total_estimate_hours'] for e in progress_data]
    
    fig.add_trace(
        go.Scatter(
            x=task_counts,
            y=time_estimates,
            mode='markers+text',
            text=epic_names,
            textposition='top center',
            name='Time vs Tasks',
            marker_size=10,
            marker_color='#9c27b0'
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        title_text="🎯 TDD Project Progress Dashboard",
        title_x=0.5,
        height=800,
        showlegend=False,
        template="plotly_white"
    )
    
    # Create HTML
    html_div = pyo.plot(fig, output_type='div', include_plotlyjs=True)
    
    # Generate Gantt chart BEFORE creating HTML
    timeline_tasks = extract_all_tasks_timeline(epics)
    gantt_chart_html = ""
    
    if timeline_tasks:
        gantt_fig = create_gantt_chart(timeline_tasks)
        if gantt_fig:
            gantt_chart_html = pyo.plot(gantt_fig, output_type='div', include_plotlyjs=False)
        else:
            gantt_chart_html = "<p><em>No timeline data available for Gantt chart.</em></p>"
    else:
        gantt_chart_html = "<p><em>No tasks found in epic files for timeline visualization.</em></p>"
    
    # Add custom styling and info
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>TDD Progress Tracker - Interactive Dashboard</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 0; 
                background: #f5f5f5;
            }}
            .header {{ 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 20px; 
                text-align: center;
            }}
            .info-panel {{ 
                background: white; 
                margin: 20px; 
                padding: 20px; 
                border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .metric {{ 
                display: inline-block; 
                margin: 10px; 
                padding: 15px; 
                background: #f8f9fa; 
                border-radius: 6px; 
                border-left: 4px solid #007bff;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 TDD Project Progress Dashboard</h1>
            <p>Real-time analytics and progress tracking</p>
        </div>
        
        <div class="info-panel">
            <div class="metric">
                <strong>Total Epics:</strong> {len(progress_data)}
            </div>
            <div class="metric">
                <strong>Total Tasks:</strong> {sum(e['total_tasks'] for e in progress_data)}
            </div>
            <div class="metric">
                <strong>Recent Commits:</strong> {git_analysis['total_commits']}
            </div>
            <div class="metric">
                <strong>Last Updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </div>
        </div>
        
        {html_div}
        
        <!-- Gantt Chart Section -->
        <div class="info-panel">
            <h3>📅 TDD Task Timeline - Gantt Chart</h3>
            <p>Interactive timeline showing all tasks with TDD phase progression and estimated durations.</p>
            <div id="gantt-chart-container">
                {gantt_chart_html}
            </div>
        </div>
        
        <div class="info-panel">
            <h3>📊 Analysis Summary</h3>
            <p><strong>Git Analysis:</strong> Found {git_analysis['total_commits']} commits in the last 30 days</p>
            <p><strong>TDD Pattern Usage:</strong> {sum(git_analysis['tdd_commits'].values())} commits follow TDD patterns</p>
            <p><strong>Average Epic Progress:</strong> {sum(e['completion_percentage'] for e in progress_data) / len(progress_data) if progress_data else 0:.1f}%</p>
            <hr>
            <p><small>🤖 Generated by TDD Project Template - Enhanced Progress Tracker</small></p>
        </div>
    </body>
    </html>
    """
    
    return full_html

def map_epic_to_section(epic_id: str, epic_name: str) -> str:
    """Map epic ID/name to mermaid.mmd sections for swimlane grouping."""
    # Based on mermaid.mmd structure
    section_mapping = {
        '0': 'Fundações',      # Epic 0 Environment and Production Safety
        '0.5': 'Fundações',    # Epic 0.5 Integration Architecture Fixes
        '2': 'Núcleo',         # Epic 2 Discovery and Compatibility
        '3': 'Núcleo',         # Epic 3 Interactive Warning System  
        '5': 'Núcleo',         # Epic 5 Cache Management Specifics
        '7': 'Núcleo',         # Epic 7 Missing Caches Integration
        '4': 'Dados e Produtividade', # Epic 4 TDAH Tooling Implementation
        '6': 'Dados e Produtividade', # Epic 6 Data Migration and Issues Integration
        '8': 'Observabilidade', # Epic 8 Task Time Monitoring and Analytics
    }
    
    # Try mapping by ID first, then by name patterns
    if epic_id in section_mapping:
        return section_mapping[epic_id]
    
    # Fallback mapping by name patterns
    name_lower = epic_name.lower()
    if any(keyword in name_lower for keyword in ['environment', 'production', 'safety', 'integration', 'architecture']):
        return 'Fundações'
    elif any(keyword in name_lower for keyword in ['discovery', 'compatibility', 'warning', 'cache']):
        return 'Núcleo'
    elif any(keyword in name_lower for keyword in ['data', 'migration', 'tdah', 'tooling', 'produtividade']):
        return 'Dados e Produtividade'  
    elif any(keyword in name_lower for keyword in ['monitoring', 'analytics', 'observability']):
        return 'Observabilidade'
    
    # Default fallback
    return 'Outros'

def extract_all_tasks_timeline(epics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract all tasks from all epics for Gantt timeline visualization with sections."""
    timeline_tasks = []
    current_date = datetime.now()
    
    # Section order for vertical positioning (top to bottom)
    section_order = ['Fundações', 'Núcleo', 'Dados e Produtividade', 'Observabilidade', 'Outros']
    
    for epic in epics:
        # Get epic information  
        epic_name = epic.get('name', epic.get('title', f"Epic {epic.get('id', 'Unknown')}"))
        epic_id = str(epic.get('id', epic.get('epic_id', 'Unknown')))
        tasks = epic.get('tasks', [])
        
        # Map epic to section for swimlane grouping
        section = map_epic_to_section(epic_id, epic_name)
        section_index = section_order.index(section) if section in section_order else len(section_order)
        
        # Start date for this epic's tasks (stagger by section)
        epic_start_date = current_date + timedelta(days=section_index * 0.2)
        
        for task in tasks:
            # Calculate duration from estimate_minutes (convert to days)
            estimate_minutes = task.get('estimate_minutes', 60)
            # Assume 8-hour work days (480 minutes), minimum 2 hours
            duration_days = max(0.25, estimate_minutes / (8 * 60))
            
            task_start_date = epic_start_date
            task_end_date = task_start_date + timedelta(days=duration_days)
            
            # Create task entry for timeline with section info
            timeline_task = {
                'Task': f"{task.get('id', task.get('task_id', 'N/A'))}: {task.get('title', 'Unnamed Task')}",
                'Start': task_start_date,
                'Finish': task_end_date,
                'Resource': epic_name,
                'Phase': task.get('tdd_phase', task.get('phase', 'analysis')),
                'Status': task.get('status', 'pending'),
                'Epic': epic_name,
                'EpicId': epic_id,
                'Section': section,
                'SectionIndex': section_index,
                'EstimateMinutes': estimate_minutes,
                'TaskId': task.get('id', task.get('task_id', 'N/A'))
            }
            
            timeline_tasks.append(timeline_task)
            
            # Next task starts when current ends (sequential within epic)
            epic_start_date = task_end_date + timedelta(hours=0.5)  # Small gap between tasks
        
        # Next epic starts with some offset
        current_date = epic_start_date + timedelta(hours=2)  # Gap between epics
    
    return timeline_tasks

def create_gantt_chart(timeline_tasks: List[Dict[str, Any]]) -> 'go.Figure':
    """Create horizontal swimlane Gantt chart similar to mermaid.mmd layout."""
    if not PLOTLY_AVAILABLE or not timeline_tasks:
        return None
    
    # Color mapping for TDD phases
    phase_color_map = {
        'red': '#f44336',      # Red phase - failing tests
        'green': '#4caf50',    # Green phase - implementation  
        'refactor': '#2196f3', # Refactor phase - optimization
        'analysis': '#ffc107'  # Analysis phase - planning
    }
    
    # Section order and positioning
    section_order = ['Fundações', 'Núcleo', 'Dados e Produtividade', 'Observabilidade', 'Outros']
    section_height = 1.0  # Height of each section lane
    lane_spacing = 0.3    # Space between sections
    
    # Group tasks by section
    tasks_by_section = {}
    for task in timeline_tasks:
        section = task.get('Section', 'Outros')
        if section not in tasks_by_section:
            tasks_by_section[section] = []
        tasks_by_section[section].append(task)
    
    # Create figure with custom layout
    fig = go.Figure()
    
    # Y-axis positions for each section (reversed for top-to-bottom order)
    section_positions = {}
    y_pos = len(section_order) - 1
    for section in section_order:
        section_positions[section] = y_pos
        y_pos -= 1
    
    # Add swimlane bars for each task
    for section, tasks in tasks_by_section.items():
        base_y = section_positions.get(section, 0)
        
        # Track lane usage within section to handle overlaps
        lane_tasks = {}  # lane_index -> list of tasks
        
        for task in tasks:
            phase = task.get('Phase', 'analysis')
            color = phase_color_map.get(phase, '#9e9e9e')
            
            # Find available lane (check for temporal overlaps)
            task_start = task['Start']
            task_end = task['Finish']
            assigned_lane = 0
            
            # Check existing lanes for overlaps
            for lane_idx, lane_task_list in lane_tasks.items():
                has_overlap = any(
                    not (task_end <= existing_task['Start'] or task_start >= existing_task['Finish'])
                    for existing_task in lane_task_list
                )
                if not has_overlap:
                    assigned_lane = lane_idx
                    break
                assigned_lane = max(assigned_lane, lane_idx + 1)
            
            # Initialize lane if needed
            if assigned_lane not in lane_tasks:
                lane_tasks[assigned_lane] = []
            lane_tasks[assigned_lane].append(task)
            
            # Calculate y position for this task (within section lane)
            task_y = base_y - (assigned_lane * 0.15)  # Offset within section
            bar_height = 0.12  # Thin bars for tasks
            
            # Add horizontal bar for this task
            fig.add_trace(go.Scatter(
                x=[task_start, task_end, task_end, task_start, task_start],
                y=[task_y - bar_height/2, task_y - bar_height/2, task_y + bar_height/2, task_y + bar_height/2, task_y - bar_height/2],
                fill='toself',
                fillcolor=color,
                line=dict(color=color, width=1),
                mode='lines',
                name=f"{phase.upper()}",
                showlegend=False,  # We'll add custom legend
                hovertemplate=(
                    f"<b>{task['Task']}</b><br>"
                    f"Section: {section}<br>"
                    f"Phase: {phase.upper()}<br>"
                    f"Epic: {task['Epic']}<br>"
                    f"Duration: {task['EstimateMinutes']} min<br>"
                    f"Start: {task_start.strftime('%Y-%m-%d %H:%M')}<br>"
                    f"End: {task_end.strftime('%Y-%m-%d %H:%M')}<br>"
                    "<extra></extra>"
                ),
                text=f"[{phase.upper()}] {task['TaskId']}"
            ))
    
    # Add section labels and dividers
    section_labels = []
    section_dividers_y = []
    for section in section_order:
        if section in tasks_by_section:
            y_pos = section_positions[section]
            section_labels.append(section)
            section_dividers_y.append(y_pos + 0.4)
            
            # Add section divider line
            fig.add_hline(
                y=y_pos + 0.4, 
                line=dict(color='lightgray', width=1, dash='dot'),
                annotation_text=section,
                annotation_position="left"
            )
    
    # Customize layout for horizontal swimlanes
    fig.update_layout(
        title=dict(
            text='📅 TDD Project Timeline - Horizontal Swimlanes',
            x=0.5,
            font=dict(size=16)
        ),
        xaxis=dict(
            title='Timeline',
            showgrid=True,
            gridcolor='lightgray',
            gridwidth=1,
            tickformat='%m/%d %H:%M'
        ),
        yaxis=dict(
            title='Project Sections',
            tickmode='array',
            tickvals=[section_positions[s] for s in section_order if s in tasks_by_section],
            ticktext=[s for s in section_order if s in tasks_by_section],
            range=[-0.5, len(section_order) - 0.5],
            automargin=True
        ),
        height=max(400, len(section_order) * 120 + 150),
        width=1200,  # Wide enough for horizontal scrolling
        margin=dict(l=200, r=50, t=80, b=50),
        template='plotly_white',
        showlegend=False
    )
    
    # Add custom legend for TDD phases
    legend_x = 0.02
    legend_y = 0.98
    for i, (phase, color) in enumerate(phase_color_map.items()):
        fig.add_annotation(
            x=legend_x + i * 0.15,
            y=legend_y,
            xref="paper",
            yref="paper",
            text=f"<span style='background-color:{color}; color:white; padding:2px 6px; border-radius:3px;'>{phase.upper()}</span>",
            showarrow=False,
            font=dict(size=11)
        )
    
    return fig

def main():
    parser = argparse.ArgumentParser(description="Generate TDD progress dashboard")
    parser.add_argument("--output", default="docs/gantt_progress.html", help="Output HTML file")
    parser.add_argument("--no-open", action="store_true", help="Don't open browser")
    args = parser.parse_args()
    
    print("📊 Generating TDD Progress Dashboard...")
    
    # Load data
    epics = load_epic_files()
    git_analysis = analyze_git_commits()
    progress_data = calculate_epic_progress(epics)
    
    print(f"📋 Found {len(epics)} epics with {len(progress_data)} analyzed")
    
    if not PLOTLY_AVAILABLE:
        print("⚠️ Plotly not available - generating fallback HTML")
    
    # Generate dashboard
    html_content = generate_interactive_html(epics, git_analysis, progress_data)
    
    # Save file
    output_path = Path(args.output)
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard generated: {output_path}")
    
    # Open browser if requested
    if not args.no_open:
        import webbrowser
        webbrowser.open(f"file://{output_path.absolute()}")

if __name__ == "__main__":
    main()