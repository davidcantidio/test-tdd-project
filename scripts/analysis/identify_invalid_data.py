#!/usr/bin/env python3
"""
Script para identificar dados faltantes e inválidos
Tarefa 1.1.1.8 - Identificar dados faltantes/inválidos
"""

import json
import os
import re
from typing import Dict, Any, List, Set, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime

def validate_epic_data(data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """Valida dados de um épico e identifica problemas"""
    
    validation_result = {
        'filename': filename,
        'is_valid': True,
        'missing_fields': [],
        'invalid_fields': [],
        'empty_fields': [],
        'suspicious_values': [],
        'task_issues': [],
        'integrity_issues': [],
        'stats': {}
    }
    
    # Determina estrutura (nested ou flat)
    if 'epic' in data:
        epic_data = data['epic']
        structure_type = 'nested'
    else:
        epic_data = data
        structure_type = 'flat'
    
    validation_result['structure_type'] = structure_type
    
    # Valida campos obrigatórios do épico
    required_epic_fields = ['id', 'name', 'tasks']
    optional_epic_fields = ['description', 'duration', 'status', 'priority']
    
    # Verifica campos obrigatórios
    for field in required_epic_fields:
        if field not in epic_data:
            validation_result['missing_fields'].append(f"epic.{field}")
            validation_result['is_valid'] = False
        elif epic_data[field] is None:
            validation_result['invalid_fields'].append({
                'field': f"epic.{field}",
                'issue': 'null_value',
                'value': None
            })
        elif isinstance(epic_data[field], str) and not epic_data[field].strip():
            validation_result['empty_fields'].append(f"epic.{field}")
    
    # Valida ID do épico
    epic_id = epic_data.get('id', epic_data.get('epic_id'))
    if epic_id:
        id_validation = validate_id_format(epic_id, 'epic')
        if not id_validation['valid']:
            validation_result['invalid_fields'].append({
                'field': 'epic.id',
                'issue': id_validation['issue'],
                'value': epic_id
            })
    
    # Valida tasks
    tasks = epic_data.get('tasks', [])
    if not isinstance(tasks, list):
        validation_result['invalid_fields'].append({
            'field': 'epic.tasks',
            'issue': 'not_array',
            'value': type(tasks).__name__
        })
    else:
        validation_result['stats']['total_tasks'] = len(tasks)
        
        # Valida cada task
        task_ids = set()
        for i, task in enumerate(tasks):
            task_validation = validate_task_data(task, i, epic_id)
            
            # Verifica duplicação de IDs
            task_id = task.get('id', task.get('task_id'))
            if task_id:
                if task_id in task_ids:
                    validation_result['integrity_issues'].append({
                        'type': 'duplicate_task_id',
                        'task_id': task_id,
                        'index': i
                    })
                task_ids.add(task_id)
            
            # Acumula problemas das tasks
            if task_validation['issues']:
                validation_result['task_issues'].extend(task_validation['issues'])
    
    # Valida integridade referencial
    integrity_issues = validate_referential_integrity(epic_data)
    validation_result['integrity_issues'].extend(integrity_issues)
    
    # Detecta valores suspeitos
    suspicious = detect_suspicious_values(epic_data)
    validation_result['suspicious_values'] = suspicious
    
    # Estatísticas adicionais
    validation_result['stats'].update({
        'empty_field_count': len(validation_result['empty_fields']),
        'missing_field_count': len(validation_result['missing_fields']),
        'invalid_field_count': len(validation_result['invalid_fields']),
        'task_issue_count': len(validation_result['task_issues']),
        'integrity_issue_count': len(validation_result['integrity_issues'])
    })
    
    return validation_result

def validate_id_format(id_value: Any, id_type: str) -> Dict[str, Any]:
    """Valida formato de IDs"""
    
    result = {'valid': True, 'issue': None}
    
    if id_value is None:
        result['valid'] = False
        result['issue'] = 'null_id'
    elif not isinstance(id_value, (str, int, float)):
        result['valid'] = False
        result['issue'] = f'invalid_type_{type(id_value).__name__}'
    else:
        id_str = str(id_value)
        
        # Verifica padrões problemáticos
        if id_str in ['[EPIC-ID]', 'X', 'X.Y', 'N/A', 'TODO', 'TBD']:
            result['valid'] = False
            result['issue'] = 'placeholder_value'
        elif len(id_str) == 0:
            result['valid'] = False
            result['issue'] = 'empty_id'
        elif len(id_str) > 50:
            result['valid'] = False
            result['issue'] = 'id_too_long'
    
    return result

def validate_task_data(task: Dict[str, Any], index: int, epic_id: Any) -> Dict[str, Any]:
    """Valida dados de uma task individual"""
    
    validation = {'issues': []}
    
    # Campos obrigatórios da task
    required_task_fields = ['id', 'title']
    recommended_task_fields = ['tdd_phase', 'estimate_minutes', 'status']
    
    # Verifica campos obrigatórios
    for field in required_task_fields:
        if field not in task and f"{field[:4]}_id" not in task:  # Permite task_id ao invés de id
            validation['issues'].append({
                'type': 'missing_task_field',
                'task_index': index,
                'field': field
            })
    
    # Valida ID da task
    task_id = task.get('id', task.get('task_id'))
    if task_id:
        id_validation = validate_id_format(task_id, 'task')
        if not id_validation['valid']:
            validation['issues'].append({
                'type': 'invalid_task_id',
                'task_index': index,
                'task_id': task_id,
                'issue': id_validation['issue']
            })
    
    # Valida TDD phase
    tdd_phase = task.get('tdd_phase', task.get('phase'))
    if tdd_phase:
        valid_phases = ['red', 'green', 'refactor', 'analysis', 'planning']
        if tdd_phase not in valid_phases and '|' not in str(tdd_phase):  # Permite múltiplas fases
            validation['issues'].append({
                'type': 'invalid_tdd_phase',
                'task_index': index,
                'task_id': task_id,
                'phase': tdd_phase
            })
    
    # Valida estimate_minutes
    estimate = task.get('estimate_minutes', task.get('estimated_time_minutes'))
    if estimate is not None:
        if not isinstance(estimate, (int, float)):
            validation['issues'].append({
                'type': 'invalid_estimate_type',
                'task_index': index,
                'task_id': task_id,
                'estimate': estimate,
                'type_found': type(estimate).__name__
            })
        elif estimate < 0:
            validation['issues'].append({
                'type': 'negative_estimate',
                'task_index': index,
                'task_id': task_id,
                'estimate': estimate
            })
        elif estimate > 10080:  # Mais de 1 semana em minutos
            validation['issues'].append({
                'type': 'excessive_estimate',
                'task_index': index,
                'task_id': task_id,
                'estimate': estimate
            })
    
    # Valida dependências
    dependencies = task.get('dependencies', task.get('depends_on', []))
    if dependencies and not isinstance(dependencies, list):
        validation['issues'].append({
            'type': 'invalid_dependencies_format',
            'task_index': index,
            'task_id': task_id,
            'dependencies': dependencies
        })
    
    # Valida deliverables
    deliverables = task.get('deliverables', [])
    if deliverables:
        if not isinstance(deliverables, list):
            validation['issues'].append({
                'type': 'invalid_deliverables_format',
                'task_index': index,
                'task_id': task_id
            })
        else:
            for i, deliverable in enumerate(deliverables):
                if deliverable is None or (isinstance(deliverable, str) and not deliverable.strip()):
                    validation['issues'].append({
                        'type': 'empty_deliverable',
                        'task_index': index,
                        'task_id': task_id,
                        'deliverable_index': i
                    })
    
    return validation

def validate_referential_integrity(epic_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Valida integridade referencial entre tasks"""
    
    issues = []
    tasks = epic_data.get('tasks', [])
    
    if not isinstance(tasks, list):
        return issues
    
    # Coleta todos os IDs de tasks
    task_ids = set()
    for task in tasks:
        task_id = task.get('id', task.get('task_id'))
        if task_id:
            task_ids.add(str(task_id))
    
    # Verifica dependências
    for i, task in enumerate(tasks):
        task_id = task.get('id', task.get('task_id'))
        dependencies = task.get('dependencies', task.get('depends_on', []))
        
        if isinstance(dependencies, list):
            for dep_id in dependencies:
                if str(dep_id) not in task_ids:
                    issues.append({
                        'type': 'missing_dependency',
                        'task_id': task_id,
                        'task_index': i,
                        'missing_dependency': dep_id,
                        'available_ids': list(task_ids)[:5]  # Primeiros 5 como exemplo
                    })
        
        # Verifica auto-referência
        if dependencies and str(task_id) in [str(d) for d in dependencies]:
            issues.append({
                'type': 'self_dependency',
                'task_id': task_id,
                'task_index': i
            })
    
    # Detecta ciclos simples de dependência
    dependency_graph = {}
    for task in tasks:
        task_id = str(task.get('id', task.get('task_id', '')))
        deps = task.get('dependencies', task.get('depends_on', []))
        if task_id and deps:
            dependency_graph[task_id] = [str(d) for d in deps]
    
    cycles = detect_dependency_cycles(dependency_graph)
    for cycle in cycles:
        issues.append({
            'type': 'dependency_cycle',
            'cycle': cycle
        })
    
    return issues

def detect_dependency_cycles(graph: Dict[str, List[str]]) -> List[List[str]]:
    """Detecta ciclos no grafo de dependências"""
    
    cycles = []
    visited = set()
    rec_stack = set()
    
    def dfs(node: str, path: List[str]) -> bool:
        if node in rec_stack:
            # Encontrou ciclo
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return True
        
        if node in visited:
            return False
        
        visited.add(node)
        rec_stack.add(node)
        
        if node in graph:
            for neighbor in graph[node]:
                if neighbor in graph:  # Só segue se o vizinho existe no grafo
                    if dfs(neighbor, path + [node]):
                        return True
        
        rec_stack.remove(node)
        return False
    
    for node in graph:
        if node not in visited:
            dfs(node, [])
    
    return cycles

def detect_suspicious_values(epic_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detecta valores suspeitos ou placeholders"""
    
    suspicious = []
    
    # Padrões suspeitos
    placeholder_patterns = [
        r'\[.*\]',  # [PLACEHOLDER]
        r'X+\.?Y*',  # X, X.Y, XXX
        r'TODO',
        r'TBD',
        r'N/A',
        r'FIXME',
        r'Lorem ipsum',
        r'test',
        r'example',
        r'template'
    ]
    
    def check_value(value: Any, path: str):
        if isinstance(value, str):
            for pattern in placeholder_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    suspicious.append({
                        'path': path,
                        'value': value[:100],  # Primeiros 100 chars
                        'pattern': pattern
                    })
                    break
        elif isinstance(value, dict):
            for key, subvalue in value.items():
                check_value(subvalue, f"{path}.{key}")
        elif isinstance(value, list):
            for i, item in enumerate(value[:10]):  # Verifica até 10 itens
                if isinstance(item, (dict, list, str)):
                    check_value(item, f"{path}[{i}]")
    
    check_value(epic_data, "epic")
    
    return suspicious

def analyze_data_quality(all_validations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analisa qualidade geral dos dados"""
    
    quality_report = {
        'total_files': len(all_validations),
        'valid_files': sum(1 for v in all_validations if v['is_valid']),
        'invalid_files': sum(1 for v in all_validations if not v['is_valid']),
        'common_issues': Counter(),
        'field_coverage': defaultdict(int),
        'data_quality_score': 0,
        'critical_issues': [],
        'recommendations': []
    }
    
    total_issues = 0
    total_fields_checked = 0
    
    for validation in all_validations:
        # Conta tipos de problemas
        if validation['missing_fields']:
            quality_report['common_issues']['missing_fields'] += len(validation['missing_fields'])
        if validation['invalid_fields']:
            quality_report['common_issues']['invalid_fields'] += len(validation['invalid_fields'])
        if validation['empty_fields']:
            quality_report['common_issues']['empty_fields'] += len(validation['empty_fields'])
        if validation['task_issues']:
            quality_report['common_issues']['task_issues'] += len(validation['task_issues'])
        if validation['integrity_issues']:
            quality_report['common_issues']['integrity_issues'] += len(validation['integrity_issues'])
        if validation['suspicious_values']:
            quality_report['common_issues']['suspicious_values'] += len(validation['suspicious_values'])
        
        # Soma total de problemas
        total_issues += sum([
            len(validation['missing_fields']),
            len(validation['invalid_fields']),
            len(validation['empty_fields']),
            len(validation['task_issues']),
            len(validation['integrity_issues'])
        ])
        
        # Estima campos verificados
        total_fields_checked += validation['stats'].get('total_tasks', 0) * 10 + 20  # Estimativa
        
        # Identifica problemas críticos
        if validation['integrity_issues']:
            for issue in validation['integrity_issues']:
                if issue['type'] in ['dependency_cycle', 'duplicate_task_id']:
                    quality_report['critical_issues'].append({
                        'file': validation['filename'],
                        'issue': issue
                    })
    
    # Calcula score de qualidade (0-100)
    if total_fields_checked > 0:
        quality_report['data_quality_score'] = max(0, 100 - (total_issues / total_fields_checked * 100))
    else:
        quality_report['data_quality_score'] = 0
    
    return quality_report

def generate_validation_report(all_validations: List[Dict[str, Any]], quality_report: Dict[str, Any]):
    """Gera relatório detalhado de validação"""
    
    print("=" * 80)
    print("🔍 RELATÓRIO DE VALIDAÇÃO DE DADOS")
    print("=" * 80)
    print()
    
    # Resumo por arquivo
    for validation in all_validations:
        filename = validation['filename']
        is_valid = "✅" if validation['is_valid'] else "❌"
        
        print(f"{is_valid} {filename}")
        print(f"   Estrutura: {validation['structure_type']}")
        print(f"   Tasks: {validation['stats'].get('total_tasks', 0)}")
        
        if validation['missing_fields']:
            print(f"   ⚠️  Campos faltantes: {len(validation['missing_fields'])}")
            for field in validation['missing_fields'][:3]:
                print(f"      - {field}")
        
        if validation['invalid_fields']:
            print(f"   ❌ Campos inválidos: {len(validation['invalid_fields'])}")
            for field_issue in validation['invalid_fields'][:3]:
                print(f"      - {field_issue['field']}: {field_issue['issue']}")
        
        if validation['task_issues']:
            print(f"   📋 Problemas em tasks: {len(validation['task_issues'])}")
            issue_types = Counter(issue['type'] for issue in validation['task_issues'])
            for issue_type, count in issue_types.most_common(3):
                print(f"      - {issue_type}: {count}")
        
        if validation['integrity_issues']:
            print(f"   🔗 Problemas de integridade: {len(validation['integrity_issues'])}")
            for issue in validation['integrity_issues'][:2]:
                print(f"      - {issue['type']}")
        
        if validation['suspicious_values']:
            print(f"   🤔 Valores suspeitos: {len(validation['suspicious_values'])}")
        
        print()
    
    # Análise de qualidade geral
    print("=" * 80)
    print("📊 ANÁLISE DE QUALIDADE DOS DADOS")
    print("=" * 80)
    print()
    
    print(f"📈 Score de Qualidade: {quality_report['data_quality_score']:.1f}/100")
    print(f"✅ Arquivos válidos: {quality_report['valid_files']}/{quality_report['total_files']}")
    print(f"❌ Arquivos inválidos: {quality_report['invalid_files']}/{quality_report['total_files']}")
    print()
    
    print("🔍 Problemas mais comuns:")
    for issue_type, count in quality_report['common_issues'].most_common():
        print(f"   • {issue_type}: {count} ocorrências")
    print()
    
    if quality_report['critical_issues']:
        print("⚠️  PROBLEMAS CRÍTICOS:")
        for critical in quality_report['critical_issues'][:5]:
            print(f"   • {critical['file']}: {critical['issue']['type']}")
    print()
    
    # Recomendações
    print("=" * 80)
    print("💡 RECOMENDAÇÕES PARA CORREÇÃO")
    print("=" * 80)
    
    recommendations = generate_data_cleaning_recommendations(all_validations, quality_report)
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print()
    print("✅ Validação de dados completa!")
    
    return recommendations

def generate_data_cleaning_recommendations(validations: List[Dict[str, Any]], quality_report: Dict[str, Any]) -> List[str]:
    """Gera recomendações para limpeza de dados"""
    
    recommendations = []
    
    # Baseado no score de qualidade
    if quality_report['data_quality_score'] < 50:
        recommendations.append("🚨 URGENTE: Qualidade crítica - revisar todos os dados antes da migração")
    elif quality_report['data_quality_score'] < 80:
        recommendations.append("⚠️  Qualidade moderada - corrigir problemas identificados antes da migração")
    
    # Placeholders
    total_suspicious = sum(len(v['suspicious_values']) for v in validations)
    if total_suspicious > 10:
        recommendations.append(f"🔄 Substituir {total_suspicious} valores placeholder por dados reais")
    
    # IDs inválidos
    invalid_id_count = sum(len([f for f in v['invalid_fields'] if 'id' in f.get('field', '')]) for v in validations)
    if invalid_id_count > 0:
        recommendations.append("🔑 Regenerar IDs inválidos com formato consistente (numérico ou UUID)")
    
    # Campos faltantes
    missing_count = quality_report['common_issues'].get('missing_fields', 0)
    if missing_count > 0:
        recommendations.append(f"📝 Adicionar {missing_count} campos obrigatórios faltantes")
    
    # Integridade referencial
    integrity_count = quality_report['common_issues'].get('integrity_issues', 0)
    if integrity_count > 0:
        recommendations.append("🔗 Corrigir referências quebradas entre tasks e dependências")
    
    # Estimativas
    recommendations.append("⏱️  Revisar e padronizar estimate_minutes (remover negativos e excessivos)")
    
    # TDD phases
    recommendations.append("🧪 Normalizar tdd_phase para valores padrão: red, green, refactor")
    
    # Campos vazios
    empty_count = quality_report['common_issues'].get('empty_fields', 0)
    if empty_count > 0:
        recommendations.append(f"✏️  Preencher {empty_count} campos vazios ou removê-los se opcionais")
    
    # Ciclos de dependência
    if any('dependency_cycle' in str(issue) for issue in quality_report.get('critical_issues', [])):
        recommendations.append("🔄 Resolver ciclos de dependência detectados")
    
    return recommendations

def main():
    """Executa validação completa de dados"""
    
    epic_files = [
        ('/home/david/Documentos/canimport/test-tdd-project/epics/epic_template.json', 'epic_template.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/epics/example_epic_0.json', 'example_epic_0.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/epics/template_epic.json', 'main_template_epic.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/tdd-project-template/epics/epic_1.json', 'epic_1.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/tdd-project-template/epics/template_epic.json', 'template_template_epic.json')
    ]
    
    print("🔍 IDENTIFICANDO DADOS FALTANTES/INVÁLIDOS - TAREFA 1.1.1.8")
    print("=" * 60)
    print()
    
    all_validations = []
    
    for file_path, filename in epic_files:
        if os.path.exists(file_path):
            print(f"🔍 Validando {filename}...")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                validation = validate_epic_data(data, filename)
                all_validations.append(validation)
                
                status = "✅" if validation['is_valid'] else "❌"
                stats = validation['stats']
                print(f"   {status} Problemas encontrados: {sum(stats.values())}")
                
            except Exception as e:
                print(f"   ❌ Erro ao processar: {e}")
                all_validations.append({
                    'filename': filename,
                    'is_valid': False,
                    'error': str(e),
                    'missing_fields': [],
                    'invalid_fields': [],
                    'empty_fields': [],
                    'suspicious_values': [],
                    'task_issues': [],
                    'integrity_issues': [],
                    'stats': {}
                })
        else:
            print(f"⚠️  Arquivo não encontrado: {filename}")
        
        print()
    
    # Análise de qualidade
    quality_report = analyze_data_quality(all_validations)
    
    # Gera relatório
    recommendations = generate_validation_report(all_validations, quality_report)
    
    return {
        'validations': all_validations,
        'quality_report': quality_report,
        'recommendations': recommendations
    }

if __name__ == "__main__":
    main()