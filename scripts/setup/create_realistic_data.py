#!/usr/bin/env python3
"""
📝 CRIAÇÃO DE DADOS REALISTAS

Converte example_epic_0.json em dados realistas para teste da migração,
removendo placeholders e criando dados válidos.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta

def create_realistic_epic():
    """Cria um épico realístico baseado no example_epic_0.json"""
    
    # Lê o arquivo base
    with open('epics/example_epic_0.json', 'r', encoding='utf-8') as f:
        base_data = json.load(f)
    
    epic_data = base_data['epic'].copy()
    
    # Converte para dados realísticos
    epic_data['id'] = 'STREAMLIT_FRAMEWORK'
    epic_data['name'] = 'Streamlit Framework Implementation'
    epic_data['summary'] = 'Implementar framework completo Streamlit com gamificação, multi-user support e integração GitHub para gerenciamento de projetos TDD.'
    
    # Remove placeholders das goals
    epic_data['goals'] = [
        'Implementar dashboard Streamlit funcional com visualizações interativas',
        'Integrar sistema de gamificação com pontos, achievements e streaks',
        'Configurar sincronização automática com GitHub Projects V2',
        'Implementar sistema multi-user com autenticação e permissões',
        'Criar sistema de time tracking integrado com TDAH-friendly metrics'
    ]
    
    epic_data['definition_of_done'] = [
        'Dashboard Streamlit funcionando com todas as visualizações',
        'Sistema de gamificação totalmente implementado e testado',
        'Integração GitHub Projects V2 sincronizando corretamente',
        'Multi-user support com controle de acesso funcional',
        'Time tracking integrado e funcionando com métricas TDAH',
        'Testes de integração passando 100%',
        'Performance atendendo targets (< 2s load time)',
        'Documentação completa e deploy realizado'
    ]
    
    epic_data['duration'] = '21 dias'
    epic_data['labels'] = ['streamlit', 'framework', 'gamification', 'github', 'multi-user']
    epic_data['status'] = 'in_progress'
    epic_data['priority'] = 1
    
    # Converte tasks realistas
    realistic_tasks = [
        {
            'id': 'SF.1',
            'title': 'Implementar dashboard principal Streamlit',
            'description': 'Criar dashboard principal com visualizações de épicos, tasks e métricas de progresso usando Streamlit e Plotly.',
            'tdd_phase': 'green',
            'status': 'completed', 
            'estimate_minutes': 180,
            'actual_minutes': 165,
            'story_points': 5,
            'acceptance_criteria': [
                'Dashboard carrega em menos de 2 segundos',
                'Todas as visualizações são interativas',
                'Dados são atualizados em tempo real'
            ],
            'deliverables': [
                'streamlit_app.py',
                'pages/dashboard.py',
                'components/metrics_widgets.py'
            ],
            'github_branch': 'feature/streamlit-dashboard',
            'github_pr_number': 42,
            'risk': 'Performance pode ser lenta com muitos dados',
            'mitigation': 'Implementar cache e paginação'
        },
        {
            'id': 'SF.2', 
            'title': 'Implementar sistema de gamificação',
            'description': 'Criar sistema completo de pontos, achievements e streaks com visualizações e notificações.',
            'tdd_phase': 'red',
            'status': 'in_progress',
            'estimate_minutes': 240,
            'actual_minutes': 120,
            'story_points': 8,
            'acceptance_criteria': [
                'Pontos calculados automaticamente por task',
                'Achievements desbloqueados baseado em ações',
                'Streaks mantidos corretamente'
            ],
            'deliverables': [
                'gamification/achievements_engine.py',
                'gamification/points_calculator.py', 
                'pages/leaderboard.py'
            ],
            'github_branch': 'feature/gamification',
            'dependencies': ['SF.1'],
            'risk': 'Complexidade das regras de gamificação',
            'mitigation': 'Começar com regras simples e iterar'
        },
        {
            'id': 'SF.3',
            'title': 'Integração GitHub Projects V2',
            'description': 'Implementar sincronização bidirecional com GitHub Projects V2 usando GraphQL API.',
            'tdd_phase': 'analysis',
            'status': 'pending',
            'estimate_minutes': 300,
            'actual_minutes': 0,
            'story_points': 8,
            'acceptance_criteria': [
                'Sincronização automática de issues e milestones',
                'Webhooks configurados e funcionando',
                'Conflict resolution implementado'
            ],
            'deliverables': [
                'github_integration/sync_engine.py',
                'github_integration/webhook_handler.py',
                'config/github_settings.py'
            ],
            'dependencies': ['SF.1', 'SF.2'],
            'risk': 'Rate limits da API do GitHub',
            'mitigation': 'Implementar cache inteligente e throttling'
        },
        {
            'id': 'SF.4',
            'title': 'Sistema multi-user com autenticação',
            'description': 'Implementar sistema de usuários com login, permissões e perfis personalizados.',
            'tdd_phase': 'analysis',
            'status': 'pending',
            'estimate_minutes': 200,
            'actual_minutes': 0,
            'story_points': 6,
            'acceptance_criteria': [
                'Login/logout funcionando',
                'Controle de acesso por role',
                'Perfis personalizáveis'
            ],
            'deliverables': [
                'auth/user_manager.py',
                'auth/permissions.py',
                'pages/profile.py'
            ],
            'dependencies': ['SF.1'],
            'risk': 'Complexidade de autenticação Streamlit',
            'mitigation': 'Usar streamlit-authenticator como base'
        },
        {
            'id': 'SF.5',
            'title': 'Time tracking com métricas TDAH',
            'description': 'Implementar sistema de time tracking com métricas específicas para TDAH (foco, energia, interrupções).',
            'tdd_phase': 'analysis', 
            'status': 'pending',
            'estimate_minutes': 180,
            'actual_minutes': 0,
            'story_points': 5,
            'acceptance_criteria': [
                'Timer integrado com interface amigável',
                'Métricas TDAH coletadas automaticamente',
                'Relatórios de produtividade disponíveis'
            ],
            'deliverables': [
                'time_tracking/timer_widget.py',
                'time_tracking/tdah_metrics.py',
                'pages/time_analytics.py'
            ],
            'dependencies': ['SF.1', 'SF.4'],
            'risk': 'Métricas TDAH podem ser invasivas',
            'mitigation': 'Fazer coleta opcional e transparente'
        }
    ]
    
    epic_data['tasks'] = realistic_tasks
    
    # Adiciona metadados realistas
    epic_data['automation_hooks'] = {
        'create_labels': epic_data['labels'],
        'project_board': {
            'name': 'Streamlit Framework Development',
            'columns': ['Backlog', 'In Progress', 'Review', 'Done']
        },
        'default_branch': 'main',
        'milestone': 'Streamlit Framework V1.0'
    }
    
    epic_data['performance_constraints'] = {
        'dashboard_load_time': '2s',
        'api_response_time': '500ms',
        'concurrent_users': 10
    }
    
    epic_data['quality_gates'] = {
        'test_coverage': '90%',
        'performance_score': '85+',
        'accessibility_score': 'AA'
    }
    
    return {'epic': epic_data}

def create_additional_epics():
    """Cria épicos adicionais para teste."""
    
    epics = []
    
    # Épico 2: Mobile Optimization
    epic_2 = {
        'epic': {
            'id': 'MOBILE_OPT',
            'name': 'Mobile Optimization',
            'summary': 'Otimizar framework para dispositivos móveis com interface responsiva e performance aprimorada.',
            'goals': [
                'Interface responsiva funcionando em todos os dispositivos',
                'Performance mobile otimizada (< 3s load time)',
                'Touch interactions implementadas corretamente'
            ],
            'definition_of_done': [
                'Layout responsivo funcionando em tablet e smartphone',
                'Performance targets atingidos em 4G',
                'Testes em dispositivos reais passando'
            ],
            'duration': '10 dias',
            'labels': ['mobile', 'responsive', 'performance'],
            'status': 'pending',
            'priority': 2,
            'tasks': [
                {
                    'id': 'MO.1',
                    'title': 'Implementar layout responsivo',
                    'description': 'Adaptar todas as páginas para funcionar em dispositivos móveis.',
                    'tdd_phase': 'analysis',
                    'status': 'pending',
                    'estimate_minutes': 120,
                    'actual_minutes': 0,
                    'story_points': 4,
                    'acceptance_criteria': [
                        'Layout funciona em telas de 320px+',
                        'Elementos são touch-friendly',
                        'Navegação mobile intuitiva'
                    ]
                },
                {
                    'id': 'MO.2',
                    'title': 'Otimizar performance mobile',
                    'description': 'Implementar lazy loading, compressão e cache para melhorar performance mobile.',
                    'tdd_phase': 'analysis',
                    'status': 'pending',
                    'estimate_minutes': 180,
                    'actual_minutes': 0,
                    'story_points': 6,
                    'acceptance_criteria': [
                        'Load time < 3s em 4G',
                        'Imagens otimizadas automaticamente',
                        'Cache funcionando corretamente'
                    ]
                }
            ]
        }
    }
    
    # Épico 3: Analytics e Reporting
    epic_3 = {
        'epic': {
            'id': 'ANALYTICS',
            'name': 'Analytics e Reporting',
            'summary': 'Implementar sistema completo de analytics e relatórios para insights de produtividade.',
            'goals': [
                'Dashboards analíticos com métricas detalhadas',
                'Relatórios exportáveis em múltiplos formatos',
                'Insights de produtividade e tendências'
            ],
            'definition_of_done': [
                'Pelo menos 5 dashboards analíticos funcionais',
                'Export para PDF, Excel e CSV funcionando',
                'Sistema de alertas implementado'
            ],
            'duration': '15 dias',
            'labels': ['analytics', 'reporting', 'insights'],
            'status': 'pending',
            'priority': 3,
            'tasks': [
                {
                    'id': 'AN.1',
                    'title': 'Dashboard de métricas de produtividade',
                    'description': 'Criar dashboard com métricas de velocity, burndown e efficiency.',
                    'tdd_phase': 'analysis',
                    'status': 'pending', 
                    'estimate_minutes': 150,
                    'actual_minutes': 0,
                    'story_points': 5,
                    'acceptance_criteria': [
                        'Métricas calculadas corretamente',
                        'Gráficos interativos funcionando',
                        'Filtros por período e usuário'
                    ]
                }
            ]
        }
    }
    
    return [epic_2, epic_3]

def save_realistic_data():
    """Salva dados realistas para migração."""
    print("📝 Criando dados realistas para migração...")
    
    # Cria épico principal
    main_epic = create_realistic_epic()
    
    # Salva épico principal
    with open('epics/streamlit_framework_epic.json', 'w', encoding='utf-8') as f:
        json.dump(main_epic, f, indent=2, ensure_ascii=False)
    
    print("  ✅ streamlit_framework_epic.json criado")
    
    # Cria épicos adicionais
    additional_epics = create_additional_epics()
    
    for i, epic in enumerate(additional_epics):
        filename = f"epics/{epic['epic']['id'].lower()}_epic.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(epic, f, indent=2, ensure_ascii=False)
        print(f"  ✅ {filename} criado")
    
    print(f"\n🎯 {len(additional_epics) + 1} épicos realistas criados")
    
    # Conta tasks totais
    total_tasks = len(main_epic['epic']['tasks'])
    for epic in additional_epics:
        total_tasks += len(epic['epic']['tasks'])
    
    print(f"📋 Total de tasks: {total_tasks}")
    
    return len(additional_epics) + 1, total_tasks

if __name__ == "__main__":
    epic_count, task_count = save_realistic_data()
    print(f"\n✅ Dados realistas prontos para migração: {epic_count} épicos, {task_count} tasks")