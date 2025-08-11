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
                if 'epic' in epic_data:
                    epics.append(epic_data['epic'])
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