#!/usr/bin/env python3
"""
Script para mapear hierarquia épico→task e relacionamentos
Tarefa 1.1.1.5 - Mapear hierarquia épico→task e relacionamentos
"""

import json
import os
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict, Counter

def analyze_task_hierarchy(data: Any, file_name: str) -> Dict[str, Any]:
    """Analisa a hierarquia de épicos e tasks em um arquivo"""
    
    result = {
        'file_name': file_name,
        'structure_type': 'unknown',
        'epic_info': {},
        'tasks': [],
        'hierarchy_analysis': {},
        'relationships': {}
    }
    
    # Determina estrutura (nested ou flat)
    if isinstance(data, dict):
        if 'epic' in data:
            # Estrutura nested (com wrapper 'epic')
            result['structure_type'] = 'nested'
            epic_data = data['epic']
        else:
            # Estrutura flat (raiz direta)
            result['structure_type'] = 'flat'
            epic_data = data
        
        # Extrai informações do épico
        result['epic_info'] = {
            'id': epic_data.get('id', epic_data.get('epic_id', 'N/A')),
            'name': epic_data.get('name', epic_data.get('title', 'N/A')),
            'description': epic_data.get('description', 'N/A'),
            'has_tasks': 'tasks' in epic_data,
            'task_count': len(epic_data.get('tasks', []))
        }
        
        # Analisa tasks
        tasks = epic_data.get('tasks', [])
        for i, task in enumerate(tasks):
            task_info = analyze_single_task(task, i, result['epic_info']['id'])
            result['tasks'].append(task_info)
        
        # Analisa hierarquia geral
        result['hierarchy_analysis'] = analyze_hierarchy_patterns(epic_data, tasks)
        
        # Analisa relacionamentos entre tasks
        result['relationships'] = analyze_task_relationships(tasks)
    
    return result

def analyze_single_task(task: Dict[str, Any], index: int, epic_id: str) -> Dict[str, Any]:
    """Analisa uma task individual"""
    
    return {
        'index': index,
        'id': task.get('id', task.get('task_id', f'task_{index}')),
        'title': task.get('title', task.get('name', 'N/A')),
        'tdd_phase': task.get('tdd_phase', task.get('phase', 'N/A')),
        'status': task.get('status', 'N/A'),
        'estimate_minutes': task.get('estimate_minutes', 0),
        'story_points': task.get('story_points', 0),
        'epic_reference': epic_id,
        'has_dependencies': 'dependencies' in task or 'depends_on' in task,
        'dependencies': task.get('dependencies', task.get('depends_on', [])),
        'has_deliverables': 'deliverables' in task,
        'deliverable_count': len(task.get('deliverables', [])),
        'has_constraints': 'performance_constraints' in task,
        'constraint_count': len(task.get('performance_constraints', [])),
        'fields_present': list(task.keys()),
        'field_count': len(task.keys())
    }

def analyze_hierarchy_patterns(epic_data: Dict[str, Any], tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analisa padrões hierárquicos no épico"""
    
    # ID patterns
    epic_id = epic_data.get('id', epic_data.get('epic_id', 'N/A'))
    task_ids = [task.get('id', task.get('task_id', '')) for task in tasks]
    
    # Verifica padrões de ID
    id_patterns = {
        'epic_id_type': type(epic_id).__name__,
        'epic_id_value': str(epic_id),
        'task_id_types': list(set(type(tid).__name__ for tid in task_ids if tid)),
        'task_id_patterns': analyze_id_patterns(task_ids),
        'hierarchical_ids': check_hierarchical_ids(epic_id, task_ids)
    }
    
    # TDD phase distribution
    phase_distribution = Counter(task.get('tdd_phase', task.get('phase', 'unknown')) for task in tasks)
    
    # Dependency analysis
    dependency_analysis = analyze_dependency_structure(tasks)
    
    return {
        'id_patterns': id_patterns,
        'phase_distribution': dict(phase_distribution),
        'dependency_structure': dependency_analysis,
        'total_estimate_minutes': sum(task.get('estimate_minutes', 0) for task in tasks),
        'total_story_points': sum(task.get('story_points', 0) for task in tasks),
        'task_complexity_distribution': analyze_task_complexity(tasks)
    }

def analyze_id_patterns(task_ids: List[str]) -> Dict[str, Any]:
    """Analisa padrões nos IDs de tasks"""
    
    patterns = {
        'numeric_only': 0,
        'alphanumeric': 0,
        'with_dots': 0,
        'with_underscores': 0,
        'hierarchical_numeric': 0,
        'examples': []
    }
    
    for tid in task_ids:
        if not tid:
            continue
            
        tid_str = str(tid)
        patterns['examples'].append(tid_str)
        
        if tid_str.isdigit():
            patterns['numeric_only'] += 1
        elif any(c.isalpha() for c in tid_str) and any(c.isdigit() for c in tid_str):
            patterns['alphanumeric'] += 1
        
        if '.' in tid_str:
            patterns['with_dots'] += 1
            # Check for hierarchical pattern like 1.1, 1.2, 2.1
            if len(tid_str.split('.')) == 2 and all(part.isdigit() for part in tid_str.split('.')):
                patterns['hierarchical_numeric'] += 1
        
        if '_' in tid_str:
            patterns['with_underscores'] += 1
    
    # Keep only first 5 examples for readability
    patterns['examples'] = patterns['examples'][:5]
    
    return patterns

def check_hierarchical_ids(epic_id: str, task_ids: List[str]) -> Dict[str, Any]:
    """Verifica se existe relação hierárquica entre épico e task IDs"""
    
    epic_str = str(epic_id)
    
    # Verifica se task IDs começam com epic ID
    prefix_matches = [tid for tid in task_ids if tid and str(tid).startswith(epic_str)]
    
    # Verifica se task IDs contêm epic ID
    contains_matches = [tid for tid in task_ids if tid and epic_str in str(tid)]
    
    return {
        'epic_id': epic_str,
        'tasks_with_epic_prefix': len(prefix_matches),
        'tasks_containing_epic_id': len(contains_matches),
        'prefix_examples': prefix_matches[:3],
        'contains_examples': contains_matches[:3],
        'is_hierarchical': len(prefix_matches) > 0 or len(contains_matches) > len(prefix_matches)
    }

def analyze_dependency_structure(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analisa estrutura de dependências entre tasks"""
    
    dependency_graph = {}
    tasks_with_deps = 0
    total_dependencies = 0
    
    for task in tasks:
        task_id = task.get('id', task.get('task_id', ''))
        dependencies = task.get('dependencies', task.get('depends_on', []))
        
        if dependencies:
            tasks_with_deps += 1
            total_dependencies += len(dependencies)
            dependency_graph[task_id] = dependencies
    
    # Detecta ciclos simples
    potential_cycles = detect_simple_cycles(dependency_graph)
    
    return {
        'tasks_with_dependencies': tasks_with_deps,
        'total_dependencies': total_dependencies,
        'average_deps_per_task': total_dependencies / len(tasks) if tasks else 0,
        'dependency_graph_sample': dict(list(dependency_graph.items())[:3]),
        'potential_cycles': potential_cycles,
        'has_dependencies': tasks_with_deps > 0
    }

def detect_simple_cycles(dep_graph: Dict[str, List[str]]) -> List[str]:
    """Detecta ciclos simples no grafo de dependências"""
    cycles = []
    
    for task_id, deps in dep_graph.items():
        for dep in deps:
            # Verifica ciclo direto (A depende de B, B depende de A)
            if dep in dep_graph and task_id in dep_graph[dep]:
                cycles.append(f"{task_id} ↔ {dep}")
    
    return list(set(cycles))  # Remove duplicatas

def analyze_task_complexity(tasks: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analisa distribuição de complexidade das tasks"""
    
    complexity_buckets = {
        'simple': 0,      # <= 30 min, <= 2 story points
        'moderate': 0,    # 31-120 min, 3-5 story points  
        'complex': 0,     # 121-480 min, 6-8 story points
        'very_complex': 0 # > 480 min, > 8 story points
    }
    
    for task in tasks:
        estimate = task.get('estimate_minutes', 0)
        story_points = task.get('story_points', 0)
        
        # Classifica baseado em estimativa de tempo (primário) e story points (secundário)
        if estimate <= 30 and story_points <= 2:
            complexity_buckets['simple'] += 1
        elif estimate <= 120 and story_points <= 5:
            complexity_buckets['moderate'] += 1
        elif estimate <= 480 and story_points <= 8:
            complexity_buckets['complex'] += 1
        else:
            complexity_buckets['very_complex'] += 1
    
    return complexity_buckets

def analyze_task_relationships(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analisa relacionamentos e padrões entre tasks"""
    
    # TDD phase transitions
    phase_transitions = analyze_tdd_transitions(tasks)
    
    # Sequential patterns (baseado em IDs ou posição)
    sequential_patterns = analyze_sequential_patterns(tasks)
    
    # Cross-references between tasks
    cross_references = analyze_cross_references(tasks)
    
    return {
        'tdd_phase_transitions': phase_transitions,
        'sequential_patterns': sequential_patterns,
        'cross_references': cross_references,
        'relationship_summary': {
            'has_sequential_ids': sequential_patterns['has_sequential'],
            'has_tdd_progression': phase_transitions['follows_tdd_order'],
            'has_cross_refs': cross_references['has_references']
        }
    }

def analyze_tdd_transitions(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analisa transições entre fases do TDD"""
    
    phases = [task.get('tdd_phase', task.get('phase', 'unknown')) for task in tasks]
    phase_transitions = []
    
    for i in range(len(phases) - 1):
        transition = f"{phases[i]} → {phases[i+1]}"
        phase_transitions.append(transition)
    
    transition_counts = Counter(phase_transitions)
    
    # Verifica se segue ordem típica do TDD
    typical_order = ['red', 'green', 'refactor']
    follows_tdd_order = check_tdd_order(phases, typical_order)
    
    return {
        'phase_sequence': phases,
        'transitions': dict(transition_counts),
        'follows_tdd_order': follows_tdd_order,
        'unique_transitions': len(transition_counts),
        'most_common_transition': transition_counts.most_common(1)[0] if transition_counts else None
    }

def check_tdd_order(phases: List[str], typical_order: List[str]) -> bool:
    """Verifica se as fases seguem ordem típica do TDD"""
    
    # Remove fases desconhecidas
    valid_phases = [p for p in phases if p in typical_order]
    
    if len(valid_phases) < 2:
        return False
    
    # Verifica se a sequência respeita a ordem típica
    last_index = -1
    for phase in valid_phases:
        current_index = typical_order.index(phase)
        if current_index < last_index:
            return False
        last_index = current_index
    
    return True

def analyze_sequential_patterns(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analisa padrões sequenciais nos IDs das tasks"""
    
    task_ids = [task.get('id', task.get('task_id', '')) for task in tasks]
    
    # Verifica IDs numéricos sequenciais
    numeric_ids = []
    for tid in task_ids:
        if tid and str(tid).isdigit():
            numeric_ids.append(int(tid))
    
    is_sequential = False
    if len(numeric_ids) > 1:
        numeric_ids.sort()
        # Verifica se são consecutivos
        is_sequential = all(numeric_ids[i] == numeric_ids[i-1] + 1 for i in range(1, len(numeric_ids)))
    
    # Verifica padrões hierárquicos (ex: 1.1, 1.2, 1.3)
    hierarchical_pattern = analyze_hierarchical_pattern(task_ids)
    
    return {
        'total_tasks': len(task_ids),
        'numeric_ids': numeric_ids,
        'has_sequential': is_sequential,
        'hierarchical_pattern': hierarchical_pattern,
        'id_examples': task_ids[:5]
    }

def analyze_hierarchical_pattern(task_ids: List[str]) -> Dict[str, Any]:
    """Analisa padrões hierárquicos nos IDs"""
    
    hierarchical_ids = []
    for tid in task_ids:
        if tid and '.' in str(tid):
            parts = str(tid).split('.')
            if len(parts) == 2 and all(part.isdigit() for part in parts):
                hierarchical_ids.append((int(parts[0]), int(parts[1])))
    
    has_hierarchical = len(hierarchical_ids) > 1
    groups = {}
    
    if has_hierarchical:
        # Agrupa por primeiro nível
        for major, minor in hierarchical_ids:
            if major not in groups:
                groups[major] = []
            groups[major].append(minor)
    
    return {
        'has_hierarchical': has_hierarchical,
        'hierarchical_count': len(hierarchical_ids),
        'groups': {k: sorted(v) for k, v in groups.items()},
        'examples': hierarchical_ids[:5]
    }

def analyze_cross_references(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analisa referências cruzadas entre tasks"""
    
    task_ids = set(str(task.get('id', task.get('task_id', ''))) for task in tasks if task.get('id') or task.get('task_id'))
    
    references_found = []
    
    for task in tasks:
        task_id = str(task.get('id', task.get('task_id', '')))
        
        # Verifica dependências
        dependencies = task.get('dependencies', task.get('depends_on', []))
        for dep in dependencies:
            if str(dep) in task_ids:
                references_found.append(f"{task_id} → {dep}")
        
        # Verifica referências em deliverables
        deliverables = task.get('deliverables', [])
        for deliverable in deliverables:
            if isinstance(deliverable, str):
                for other_id in task_ids:
                    if other_id != task_id and other_id in deliverable:
                        references_found.append(f"{task_id} refs {other_id} in deliverable")
    
    return {
        'has_references': len(references_found) > 0,
        'total_references': len(references_found),
        'reference_examples': references_found[:5],
        'task_ids_available': list(task_ids)[:5]
    }

def analyze_all_files() -> Dict[str, Any]:
    """Analisa hierarquia em todos os arquivos épicos"""
    
    epic_files = [
        ('/home/david/Documentos/canimport/test-tdd-project/epics/epic_template.json', 'epic_template.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/epics/example_epic_0.json', 'example_epic_0.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/epics/template_epic.json', 'main_template_epic.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/tdd-project-template/epics/epic_1.json', 'epic_1.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/tdd-project-template/epics/template_epic.json', 'template_template_epic.json')
    ]
    
    analysis_results = {}
    
    print("📋 MAPEANDO HIERARQUIA ÉPICO→TASK - TAREFA 1.1.1.5")
    print("=" * 60)
    print()
    
    for file_path, filename in epic_files:
        if os.path.exists(file_path):
            print(f"📄 Analisando hierarquia em {filename}...")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                analysis = analyze_task_hierarchy(data, filename)
                analysis_results[filename] = analysis
                
                # Resumo rápido
                epic_info = analysis['epic_info']
                tasks_count = len(analysis['tasks'])
                has_deps = analysis['relationships']['relationship_summary']['has_cross_refs']
                
                print(f"   ✅ Épico ID: {epic_info['id']} | Tasks: {tasks_count} | Dependências: {has_deps}")
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
        else:
            print(f"⚠️  Arquivo não encontrado: {filename}")
        
        print()
    
    return analysis_results

def generate_hierarchy_report(analysis_results: Dict[str, Any]):
    """Gera relatório detalhado da hierarquia"""
    
    print("=" * 80)
    print("🏗️  RELATÓRIO DE HIERARQUIA ÉPICO→TASK")
    print("=" * 80)
    print()
    
    # Análise por arquivo
    for filename, analysis in analysis_results.items():
        print(f"📁 {filename}")
        print("-" * 50)
        
        epic_info = analysis['epic_info']
        hierarchy = analysis['hierarchy_analysis']
        relationships = analysis['relationships']
        
        print(f"🎯 Épico: {epic_info['id']} - {epic_info['name']}")
        print(f"📊 Estrutura: {analysis['structure_type']}")
        print(f"📋 Tasks: {epic_info['task_count']}")
        
        # ID patterns
        id_patterns = hierarchy['id_patterns']
        print(f"🔢 Padrão de IDs: {id_patterns['epic_id_type']} | Hierárquico: {id_patterns['hierarchical_ids']['is_hierarchical']}")
        
        # TDD phases
        phase_dist = hierarchy['phase_distribution']
        print(f"🧪 Fases TDD: {dict(phase_dist)}")
        
        # Dependencies
        dep_structure = hierarchy['dependency_structure']
        print(f"🔗 Dependências: {dep_structure['tasks_with_dependencies']}/{epic_info['task_count']} tasks")
        
        # Relationships
        rel_summary = relationships['relationship_summary']
        print(f"⚡ Relacionamentos: IDs sequenciais: {rel_summary['has_sequential_ids']}, Progressão TDD: {rel_summary['has_tdd_progression']}")
        
        print()
    
    # Análise consolidada
    print("=" * 80)
    print("📊 ANÁLISE CONSOLIDADA")
    print("=" * 80)
    
    # Estruturas encontradas
    structure_types = [analysis['structure_type'] for analysis in analysis_results.values()]
    structure_count = Counter(structure_types)
    
    print(f"🏗️  Tipos de estrutura encontrados:")
    for struct_type, count in structure_count.items():
        print(f"   • {struct_type}: {count} arquivos")
    print()
    
    # Padrões de ID
    hierarchical_count = sum(1 for analysis in analysis_results.values() 
                           if analysis['hierarchy_analysis']['id_patterns']['hierarchical_ids']['is_hierarchical'])
    
    print(f"🔢 Padrões de ID:")
    print(f"   • Hierárquicos: {hierarchical_count}/{len(analysis_results)} arquivos")
    print(f"   • Flat: {len(analysis_results) - hierarchical_count}/{len(analysis_results)} arquivos")
    print()
    
    # Análise de dependências
    files_with_deps = sum(1 for analysis in analysis_results.values()
                         if analysis['hierarchy_analysis']['dependency_structure']['has_dependencies'])
    
    total_tasks = sum(analysis['epic_info']['task_count'] for analysis in analysis_results.values())
    total_deps = sum(analysis['hierarchy_analysis']['dependency_structure']['total_dependencies'] 
                    for analysis in analysis_results.values())
    
    print(f"🔗 Análise de dependências:")
    print(f"   • Arquivos com dependências: {files_with_deps}/{len(analysis_results)}")
    print(f"   • Total de dependências: {total_deps}")
    print(f"   • Média de dependências por task: {total_deps/total_tasks:.2f}" if total_tasks > 0 else "   • Média: 0")
    print()
    
    # Fases TDD mais comuns
    all_phases = []
    for analysis in analysis_results.values():
        phase_dist = analysis['hierarchy_analysis']['phase_distribution']
        for phase, count in phase_dist.items():
            all_phases.extend([phase] * count)
    
    phase_counter = Counter(all_phases)
    print(f"🧪 Distribuição geral de fases TDD:")
    for phase, count in phase_counter.most_common():
        percentage = (count / len(all_phases)) * 100 if all_phases else 0
        print(f"   • {phase}: {count} tasks ({percentage:.1f}%)")
    print()
    
    # Recomendações para migração
    print("=" * 80)
    print("💡 RECOMENDAÇÕES PARA MIGRAÇÃO")
    print("=" * 80)
    
    print("1. 🔄 Normalização de estrutura:")
    if structure_count['nested'] > 0 and structure_count.get('flat', 0) > 0:
        print("   ⚠️  Estruturas mistas encontradas - unificar para um padrão")
    else:
        print("   ✅ Estrutura consistente")
    
    print("\n2. 🔢 Padronização de IDs:")
    if hierarchical_count < len(analysis_results):
        print("   ⚠️  Implementar padrão hierárquico consistente (ex: epic.task)")
    else:
        print("   ✅ IDs já seguem padrão hierárquico")
    
    print("\n3. 🔗 Mapeamento de relacionamentos:")
    if total_deps > 0:
        print("   ✅ Sistema já usa dependências - mapear para foreign keys")
    else:
        print("   ⚠️  Implementar sistema de dependências explícitas")
    
    print("\n4. 🧪 Integridade TDD:")
    if 'unknown' in phase_counter:
        print("   ⚠️  Padronizar fases TDD (red/green/refactor)")
    else:
        print("   ✅ Fases TDD bem definidas")
    
    print()
    print("✅ Mapeamento de hierarquia completo!")
    
    return {
        'structure_analysis': structure_count,
        'id_patterns': {'hierarchical_files': hierarchical_count},
        'dependency_analysis': {'files_with_deps': files_with_deps, 'total_deps': total_deps},
        'phase_distribution': dict(phase_counter),
        'migration_readiness': {
            'structure_consistent': len(structure_count) == 1,
            'ids_hierarchical': hierarchical_count == len(analysis_results),
            'has_dependencies': total_deps > 0,
            'phases_standardized': 'unknown' not in phase_counter
        }
    }

def main():
    """Executa análise completa de hierarquia épico→task"""
    analysis_results = analyze_all_files()
    summary = generate_hierarchy_report(analysis_results)
    
    # Retorna resultados para próximas etapas
    return {
        'detailed_analysis': analysis_results,
        'summary': summary
    }

if __name__ == "__main__":
    main()