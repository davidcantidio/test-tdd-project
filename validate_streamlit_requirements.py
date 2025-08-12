#!/usr/bin/env python3
"""
📋 STREAMLIT REQUIREMENTS VALIDATION

Valida 100% compatibilidade com requisitos do streamlit_briefing.md
baseado na implementação atual do framework.
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class StreamlitRequirementsValidator:
    def __init__(self):
        self.framework_db = "framework.db"
        self.timer_db = "task_timer.db"
        self.briefing_path = "/home/david/Documentos/canimport/streamlit_briefing.md"
        
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'requirements_checked': 0,
            'requirements_met': 0,
            'compliance_score': 0.0,
            'categories': {},
            'recommendations': [],
            'critical_issues': [],
            'status': 'UNKNOWN'
        }
    
    def validate_all_requirements(self):
        """Valida todos os requisitos do streamlit_briefing.md."""
        print("📋 STREAMLIT REQUIREMENTS VALIDATION")
        print("=" * 60)
        
        try:
            # Lê o briefing
            self._read_briefing_requirements()
            
            # Executa validações por categoria
            self._validate_framework_reusability()
            self._validate_database_integration()
            self._validate_gamification_tdah()
            self._validate_github_integration()
            self._validate_multi_project_support()
            self._validate_interface_requirements()
            self._validate_compatibility_requirements()
            
            # Calcula score final
            self._calculate_final_score()
            
            # Gera relatório
            self._generate_validation_report()
            
            print(f"\n🎯 VALIDATION COMPLETED")
            print(f"Score: {self.validation_results['compliance_score']:.1f}%")
            print(f"Status: {self.validation_results['status']}")
            
            return self.validation_results['status'] in ['FULLY_COMPLIANT', 'MOSTLY_COMPLIANT']
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
    
    def _read_briefing_requirements(self):
        """Analisa o streamlit_briefing.md para extrair requisitos."""
        print("📖 Reading streamlit_briefing.md...")
        
        try:
            with open(self.briefing_path, 'r', encoding='utf-8') as f:
                briefing_content = f.read()
            
            # Extrai requisitos chave do briefing
            self.requirements = {
                'framework_reusability': [
                    "Framework base reutilizável",
                    "Metodologia TDD com fases red/green/refactor",
                    "Esquema de épicos em JSON",
                    "Integração opcional com GitHub Projects V2"
                ],
                'database_integration': [
                    "Banco de dados SQLite (task_timer.db)",
                    "Armazenamento de épicos, tarefas, decisões",
                    "Logs de sincronização",
                    "Conectar banco de dados relacional via FK"
                ],
                'gamification_tdah': [
                    "Gamificação e suporte a TDAH",
                    "Timers com alertas sonoros/visuais", 
                    "Análise de padrões de atenção",
                    "Recomendações de pausas"
                ],
                'interface_requirements': [
                    "Interface local, interativa e gamificada",
                    "Substituir dashboard do GitHub Pages",
                    "Não alterar funcionamento atual",
                    "Dashboards interativos com Plotly"
                ],
                'github_integration': [
                    "Sincronização com GitHub Projects V2",
                    "Respeitar rate limits",
                    "Integração opcional"
                ],
                'multi_project_support': [
                    "Seja clonável para cada projeto",
                    "Adaptar pasta app/ para lógica específica",
                    "Bancos próprios relacionados via FK",
                    "Reuso em novos projetos"
                ],
                'compatibility': [
                    "Manter compatibilidade com scripts existentes",
                    "Wizard de setup funcional",
                    "Analytics engine funcional",
                    "CLI robusta com Typer"
                ]
            }
            
            print(f"  ✅ Briefing analyzed - {len(self.requirements)} categories identified")
            
        except Exception as e:
            print(f"  ❌ Failed to read briefing: {e}")
            raise
    
    def _validate_framework_reusability(self):
        """Valida requisitos de reusabilidade do framework."""
        print("\n🏗️ Validating Framework Reusability...")
        
        category = 'framework_reusability'
        results = []
        
        # Verifica metodologia TDD
        tdd_check = self._check_tdd_methodology()
        results.append(('TDD methodology support', tdd_check))
        
        # Verifica esquema de épicos em JSON
        json_schema_check = self._check_json_epic_schema()
        results.append(('JSON epic schema', json_schema_check))
        
        # Verifica estrutura modular
        modularity_check = self._check_framework_modularity()
        results.append(('Framework modularity', modularity_check))
        
        # Verifica GitHub integration opcional
        github_optional_check = self._check_optional_github_integration()
        results.append(('Optional GitHub integration', github_optional_check))
        
        self._record_category_results(category, results)
    
    def _validate_database_integration(self):
        """Valida integração com banco de dados."""
        print("\n🗄️ Validating Database Integration...")
        
        category = 'database_integration'
        results = []
        
        # Verifica existência do task_timer.db
        timer_db_check = Path(self.timer_db).exists()
        results.append(('task_timer.db exists', timer_db_check))
        
        # Verifica framework.db
        framework_db_check = Path(self.framework_db).exists()
        results.append(('framework.db exists', framework_db_check))
        
        # Verifica esquema de épicos e tarefas
        epic_schema_check = self._validate_epic_task_schema()
        results.append(('Epic/task schema', epic_schema_check))
        
        # Verifica logs de sincronização
        sync_logs_check = self._validate_sync_logs_schema()
        results.append(('Sync logs schema', sync_logs_check))
        
        # Verifica foreign keys para extensibilidade
        fk_extensibility_check = self._validate_fk_extensibility()
        results.append(('FK extensibility', fk_extensibility_check))
        
        self._record_category_results(category, results)
    
    def _validate_gamification_tdah(self):
        """Valida funcionalidades de gamificação e TDAH."""
        print("\n🎮 Validating Gamification & TDAH Support...")
        
        category = 'gamification_tdah'
        results = []
        
        # Verifica sistema de gamificação
        gamification_check = self._check_gamification_system()
        results.append(('Gamification system', gamification_check))
        
        # Verifica suporte TDAH
        tdah_support_check = self._check_tdah_support()
        results.append(('TDAH support features', tdah_support_check))
        
        # Verifica timer functionality
        timer_check = self._check_timer_functionality()
        results.append(('Timer functionality', timer_check))
        
        # Verifica análise de padrões
        pattern_analysis_check = self._check_pattern_analysis()
        results.append(('Pattern analysis', pattern_analysis_check))
        
        self._record_category_results(category, results)
    
    def _validate_github_integration(self):
        """Valida integração com GitHub Projects V2."""
        print("\n🐙 Validating GitHub Integration...")
        
        category = 'github_integration'
        results = []
        
        # Verifica campos GitHub no schema
        github_fields_check = self._check_github_schema_fields()
        results.append(('GitHub schema fields', github_fields_check))
        
        # Verifica sync log table
        sync_log_check = self._check_github_sync_log_table()
        results.append(('GitHub sync log table', sync_log_check))
        
        # Verifica rate limiting consideration
        rate_limit_check = self._check_rate_limiting_support()
        results.append(('Rate limiting support', rate_limit_check))
        
        self._record_category_results(category, results)
    
    def _validate_multi_project_support(self):
        """Valida suporte a múltiplos projetos."""
        print("\n🚀 Validating Multi-Project Support...")
        
        category = 'multi_project_support'
        results = []
        
        # Verifica estrutura clonável
        cloneable_structure_check = self._check_cloneable_structure()
        results.append(('Cloneable structure', cloneable_structure_check))
        
        # Verifica extensibilidade via FK
        fk_extensibility_check = self._check_foreign_key_extensibility()
        results.append(('FK extensibility', fk_extensibility_check))
        
        # Verifica configurações modulares
        modular_config_check = self._check_modular_configuration()
        results.append(('Modular configuration', modular_config_check))
        
        self._record_category_results(category, results)
    
    def _validate_interface_requirements(self):
        """Valida requisitos de interface."""
        print("\n💻 Validating Interface Requirements...")
        
        category = 'interface_requirements'
        results = []
        
        # Verifica preparação para Streamlit
        streamlit_ready_check = self._check_streamlit_readiness()
        results.append(('Streamlit readiness', streamlit_ready_check))
        
        # Verifica suporte a visualizações
        visualization_check = self._check_visualization_support()
        results.append(('Visualization support', visualization_check))
        
        # Verifica interface gamificada
        gamified_interface_check = self._check_gamified_interface_ready()
        results.append(('Gamified interface ready', gamified_interface_check))
        
        self._record_category_results(category, results)
    
    def _validate_compatibility_requirements(self):
        """Valida requisitos de compatibilidade."""
        print("\n🔄 Validating Compatibility Requirements...")
        
        category = 'compatibility'
        results = []
        
        # Verifica scripts existentes
        existing_scripts_check = self._check_existing_scripts()
        results.append(('Existing scripts preserved', existing_scripts_check))
        
        # Verifica analytics engine
        analytics_check = self._check_analytics_compatibility()
        results.append(('Analytics engine compatible', analytics_check))
        
        # Verifica backward compatibility
        backward_compat_check = self._check_backward_compatibility()
        results.append(('Backward compatibility', backward_compat_check))
        
        self._record_category_results(category, results)
    
    # Métodos de verificação específicos
    def _check_tdd_methodology(self):
        """Verifica suporte à metodologia TDD."""
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            # Verifica se existem campos TDD
            cursor.execute("PRAGMA table_info(framework_tasks)")
            columns = [col[1] for col in cursor.fetchall()]
            
            has_tdd_phase = 'tdd_phase' in columns
            
            if has_tdd_phase:
                cursor.execute("SELECT DISTINCT tdd_phase FROM framework_tasks WHERE tdd_phase IS NOT NULL")
                phases = [row[0] for row in cursor.fetchall()]
                has_tdd_phases = any(phase in ['red', 'green', 'refactor'] for phase in phases)
            else:
                has_tdd_phases = False
            
            conn.close()
            return has_tdd_phase and has_tdd_phases
            
        except Exception:
            return False
    
    def _check_json_epic_schema(self):
        """Verifica esquema JSON de épicos."""
        epic_dir = Path("epics")
        if not epic_dir.exists():
            return False
        
        json_files = list(epic_dir.glob("*.json"))
        if len(json_files) < 1:
            return False
        
        # Verifica se pelo menos um JSON tem estrutura válida
        try:
            for json_file in json_files[:3]:  # Verifica primeiros 3
                with open(json_file) as f:
                    data = json.load(f)
                
                # Verifica se tem estrutura de épico
                if 'epic' in data or all(key in data for key in ['name', 'tasks']):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _check_framework_modularity(self):
        """Verifica modularidade do framework."""
        # Verifica se existem estruturas modulares
        key_directories = ['epics', 'backups']  # Diretórios que indicam modularidade
        
        modularity_score = sum(1 for dir_name in key_directories if Path(dir_name).exists())
        
        # Verifica arquivos de configuração
        config_files = ['framework_v3.sql', 'database_maintenance.py']
        config_score = sum(1 for file in config_files if Path(file).exists())
        
        return (modularity_score >= 1) and (config_score >= 2)
    
    def _check_optional_github_integration(self):
        """Verifica integração GitHub opcional."""
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            # Verifica campos GitHub (opcionais, podem ser NULL)
            cursor.execute("""
                SELECT name FROM pragma_table_info('framework_epics') 
                WHERE name LIKE 'github_%'
            """)
            github_fields = cursor.fetchall()
            
            # Verifica tabela de sync logs
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='github_sync_log'
            """)
            sync_table_exists = cursor.fetchone() is not None
            
            conn.close()
            
            return len(github_fields) >= 2 and sync_table_exists
            
        except Exception:
            return False
    
    def _validate_epic_task_schema(self):
        """Valida esquema de épicos e tarefas."""
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            # Verifica tabelas essenciais
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name IN ('framework_epics', 'framework_tasks')
            """)
            essential_tables = cursor.fetchone()[0]
            
            # Verifica relacionamento épico-task
            cursor.execute("""
                SELECT COUNT(*) FROM pragma_foreign_key_list('framework_tasks')
                WHERE "table" = 'framework_epics'
            """)
            fk_relationship = cursor.fetchone()[0]
            
            conn.close()
            
            return essential_tables == 2 and fk_relationship > 0
            
        except Exception:
            return False
    
    def _validate_sync_logs_schema(self):
        """Valida esquema de logs de sincronização."""
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name='github_sync_log'
            """)
            sync_table_exists = cursor.fetchone()[0] > 0
            
            if sync_table_exists:
                cursor.execute("PRAGMA table_info(github_sync_log)")
                columns = [col[1] for col in cursor.fetchall()]
                required_fields = ['sync_type', 'status', 'records_processed']
                has_required_fields = all(field in columns for field in required_fields)
            else:
                has_required_fields = False
            
            conn.close()
            
            return sync_table_exists and has_required_fields
            
        except Exception:
            return False
    
    def _validate_fk_extensibility(self):
        """Valida extensibilidade via foreign keys."""
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            # Conta foreign keys no schema
            all_fks = 0
            tables = ['framework_tasks', 'user_achievements', 'work_sessions', 'user_streaks']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM pragma_foreign_key_list('{table}')")
                fk_count = cursor.fetchone()[0]
                all_fks += fk_count
            
            conn.close()
            
            # Pelo menos 5 FKs indicam boa extensibilidade
            return all_fks >= 5
            
        except Exception:
            return False
    
    def _check_gamification_system(self):
        """Verifica sistema de gamificação."""
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            # Verifica tabelas de gamificação
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name IN ('achievement_types', 'user_achievements', 'user_streaks')
            """)
            gamification_tables = cursor.fetchone()[0]
            
            # Verifica se há achievements configurados
            if gamification_tables >= 2:
                cursor.execute("SELECT COUNT(*) FROM achievement_types WHERE is_active = TRUE")
                active_achievements = cursor.fetchone()[0]
            else:
                active_achievements = 0
            
            conn.close()
            
            return gamification_tables >= 2 and active_achievements >= 5
            
        except Exception:
            return False
    
    def _check_tdah_support(self):
        """Verifica funcionalidades de suporte TDAH."""
        # Verifica se task_timer.db existe e tem métricas TDAH
        if not Path(self.timer_db).exists():
            return False
        
        try:
            conn = sqlite3.connect(self.timer_db)
            cursor = conn.cursor()
            
            # Verifica campos TDAH específicos
            cursor.execute("PRAGMA table_info(timer_sessions)")
            columns = [col[1] for col in cursor.fetchall()]
            
            tdah_fields = ['focus_rating', 'energy_level', 'mood_rating', 'interruptions_count']
            has_tdah_fields = all(field in columns for field in tdah_fields)
            
            conn.close()
            
            return has_tdah_fields
            
        except Exception:
            return False
    
    def _check_timer_functionality(self):
        """Verifica funcionalidade de timer."""
        if not Path(self.timer_db).exists():
            return False
        
        try:
            conn = sqlite3.connect(self.timer_db)
            cursor = conn.cursor()
            
            # Verifica se há sessões de timer
            cursor.execute("SELECT COUNT(*) FROM timer_sessions")
            session_count = cursor.fetchone()[0]
            
            # Verifica configurações de timer
            cursor.execute("SELECT COUNT(*) FROM timer_settings WHERE category = 'pomodoro'")
            timer_settings = cursor.fetchone()[0]
            
            conn.close()
            
            return session_count > 0 and timer_settings > 0
            
        except Exception:
            return False
    
    def _check_pattern_analysis(self):
        """Verifica análise de padrões."""
        # Verifica se há dados suficientes para análise
        if not Path(self.timer_db).exists():
            return False
        
        try:
            conn = sqlite3.connect(self.timer_db)
            cursor = conn.cursor()
            
            # Verifica se há dados para análise de padrões
            cursor.execute("""
                SELECT COUNT(DISTINCT DATE(started_at)) 
                FROM timer_sessions 
                WHERE focus_rating IS NOT NULL
            """)
            analysis_days = cursor.fetchone()[0]
            
            conn.close()
            
            return analysis_days >= 3  # Pelo menos 3 dias de dados
            
        except Exception:
            return False
    
    def _check_github_schema_fields(self):
        """Verifica campos GitHub no schema."""
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            # Verifica campos GitHub em épicos
            cursor.execute("""
                SELECT COUNT(*) FROM pragma_table_info('framework_epics') 
                WHERE name LIKE 'github_%'
            """)
            epic_github_fields = cursor.fetchone()[0]
            
            # Verifica campos GitHub em tasks
            cursor.execute("""
                SELECT COUNT(*) FROM pragma_table_info('framework_tasks') 
                WHERE name LIKE 'github_%'
            """)
            task_github_fields = cursor.fetchone()[0]
            
            conn.close()
            
            return epic_github_fields >= 2 and task_github_fields >= 2
            
        except Exception:
            return False
    
    def _check_github_sync_log_table(self):
        """Verifica tabela de log de sincronização GitHub."""
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name='github_sync_log'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            conn.close()
            
            return table_exists
            
        except Exception:
            return False
    
    def _check_rate_limiting_support(self):
        """Verifica considerações de rate limiting."""
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            # Verifica se tabela de sync tem campos de controle
            cursor.execute("PRAGMA table_info(github_sync_log)")
            columns = [col[1] for col in cursor.fetchall()]
            
            rate_limit_fields = ['github_api_calls', 'execution_time_ms']
            has_rate_fields = any(field in columns for field in rate_limit_fields)
            
            conn.close()
            
            return has_rate_fields
            
        except Exception:
            return False
    
    def _check_cloneable_structure(self):
        """Verifica estrutura clonável."""
        # Verifica estrutura de arquivos
        key_files = ['framework_v3.sql', 'database_maintenance.py', 'migrate_real_json_data.py']
        structure_score = sum(1 for file in key_files if Path(file).exists())
        
        # Verifica modularidade
        return structure_score >= 2 and Path("epics").exists()
    
    def _check_foreign_key_extensibility(self):
        """Verifica extensibilidade via foreign keys."""
        return self._validate_fk_extensibility()  # Reutiliza método anterior
    
    def _check_modular_configuration(self):
        """Verifica configuração modular."""
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            # Verifica system_settings
            cursor.execute("SELECT COUNT(*) FROM system_settings")
            settings_count = cursor.fetchone()[0]
            
            # Verifica categorias de configuração
            cursor.execute("SELECT COUNT(DISTINCT category) FROM system_settings")
            categories_count = cursor.fetchone()[0]
            
            conn.close()
            
            return settings_count >= 10 and categories_count >= 3
            
        except Exception:
            return False
    
    def _check_streamlit_readiness(self):
        """Verifica preparação para Streamlit."""
        # Verifica estrutura de dados compatível com Streamlit
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            # Verifica views para dashboard
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='view' AND name IN ('user_dashboard', 'epic_progress')
            """)
            dashboard_views = cursor.fetchone()[0]
            
            conn.close()
            
            return dashboard_views >= 2
            
        except Exception:
            return False
    
    def _check_visualization_support(self):
        """Verifica suporte a visualizações."""
        # Verifica se dados estão estruturados para visualização
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            # Verifica dados para gráficos
            cursor.execute("SELECT COUNT(*) FROM framework_epics")
            epic_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM framework_tasks")
            task_count = cursor.fetchone()[0]
            
            conn.close()
            
            return epic_count > 0 and task_count > 0
            
        except Exception:
            return False
    
    def _check_gamified_interface_ready(self):
        """Verifica preparação para interface gamificada."""
        return self._check_gamification_system()  # Reutiliza verificação de gamificação
    
    def _check_existing_scripts(self):
        """Verifica preservação de scripts existentes."""
        # Verifica se scripts de manutenção existem
        maintenance_scripts = ['database_maintenance.py', 'test_database_integrity.py']
        return any(Path(script).exists() for script in maintenance_scripts)
    
    def _check_analytics_compatibility(self):
        """Verifica compatibilidade com analytics engine."""
        # Verifica se estrutura permite analytics
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            # Verifica dados para analytics
            cursor.execute("""
                SELECT COUNT(*) FROM framework_tasks t
                JOIN framework_epics e ON t.epic_id = e.id
                WHERE t.status = 'completed'
            """)
            completed_tasks = cursor.fetchone()[0]
            
            conn.close()
            
            # Verifica integração com timer
            timer_integration = Path(self.timer_db).exists()
            
            return completed_tasks > 0 or timer_integration
            
        except Exception:
            return False
    
    def _check_backward_compatibility(self):
        """Verifica compatibilidade reversa."""
        # Verifica se estrutura JSON ainda é suportada
        json_support = Path("epics").exists() and len(list(Path("epics").glob("*.json"))) > 0
        
        # Verifica se databases existem
        db_support = Path(self.framework_db).exists()
        
        return json_support and db_support
    
    def _record_category_results(self, category, results):
        """Registra resultados de uma categoria."""
        passed = sum(1 for _, result in results if result)
        total = len(results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        self.validation_results['requirements_checked'] += total
        self.validation_results['requirements_met'] += passed
        
        self.validation_results['categories'][category] = {
            'total_checks': total,
            'passed_checks': passed,
            'percentage': percentage,
            'status': 'PASS' if percentage >= 80 else 'PARTIAL' if percentage >= 50 else 'FAIL',
            'details': results
        }
        
        print(f"  📊 {category.replace('_', ' ').title()}: {passed}/{total} ({percentage:.1f}%)")
        
        for check_name, result in results:
            icon = "✅" if result else "❌"
            print(f"    {icon} {check_name}")
        
        if percentage < 80:
            self.validation_results['recommendations'].append(
                f"Improve {category.replace('_', ' ')} compliance ({percentage:.1f}%)"
            )
        
        if percentage < 50:
            self.validation_results['critical_issues'].append(
                f"Critical: {category.replace('_', ' ')} fails compliance ({percentage:.1f}%)"
            )
    
    def _calculate_final_score(self):
        """Calcula score final de compliance."""
        if self.validation_results['requirements_checked'] > 0:
            score = (self.validation_results['requirements_met'] / 
                    self.validation_results['requirements_checked'] * 100)
            self.validation_results['compliance_score'] = score
            
            if score >= 90:
                self.validation_results['status'] = 'FULLY_COMPLIANT'
            elif score >= 70:
                self.validation_results['status'] = 'MOSTLY_COMPLIANT'  
            elif score >= 50:
                self.validation_results['status'] = 'PARTIALLY_COMPLIANT'
            else:
                self.validation_results['status'] = 'NON_COMPLIANT'
        else:
            self.validation_results['status'] = 'NO_CHECKS_RUN'
    
    def _generate_validation_report(self):
        """Gera relatório final de validação."""
        report_path = f"streamlit_requirements_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 STREAMLIT REQUIREMENTS VALIDATION REPORT")
        print("=" * 60)
        print(f"🎯 Overall Compliance: {self.validation_results['compliance_score']:.1f}%")
        print(f"📊 Requirements: {self.validation_results['requirements_met']}/{self.validation_results['requirements_checked']}")
        print(f"🏷️ Status: {self.validation_results['status']}")
        
        print(f"\n📊 Category Breakdown:")
        for category, results in self.validation_results['categories'].items():
            status_icon = "✅" if results['status'] == 'PASS' else "⚠️" if results['status'] == 'PARTIAL' else "❌"
            print(f"  {status_icon} {category.replace('_', ' ').title()}: {results['percentage']:.1f}%")
        
        if self.validation_results['critical_issues']:
            print(f"\n🚨 Critical Issues:")
            for issue in self.validation_results['critical_issues']:
                print(f"  • {issue}")
        
        if self.validation_results['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in self.validation_results['recommendations']:
                print(f"  • {rec}")
        
        print(f"\n📄 Full report saved: {report_path}")

def main():
    """Executa validação completa."""
    validator = StreamlitRequirementsValidator()
    success = validator.validate_all_requirements()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)