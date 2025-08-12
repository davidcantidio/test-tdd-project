#!/usr/bin/env python3
"""
⏰ TASK TIMER DATABASE STUB

Cria task_timer.db stub para testes realistas de integração.
"""

import sqlite3
import json
from datetime import datetime, timedelta
import random

def create_task_timer_db():
    """Cria task_timer.db com estrutura realista."""
    print("⏰ Criando task_timer.db stub...")
    
    conn = sqlite3.connect('task_timer.db')
    cursor = conn.cursor()
    
    # Schema do task timer
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timer_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_reference VARCHAR(100),  -- Referência para framework.db
            user_identifier VARCHAR(50),
            
            -- Session timing
            started_at TIMESTAMP NOT NULL,
            ended_at TIMESTAMP,
            planned_duration_minutes INTEGER DEFAULT 25,  -- Pomodoro default
            actual_duration_minutes INTEGER,
            
            -- TDAH-friendly metrics
            focus_rating INTEGER CHECK(focus_rating BETWEEN 1 AND 10),
            energy_level INTEGER CHECK(energy_level BETWEEN 1 AND 10),
            mood_rating INTEGER CHECK(mood_rating BETWEEN 1 AND 10),
            interruptions_count INTEGER DEFAULT 0,
            
            -- Environment context
            environment VARCHAR(50),  -- 'home', 'office', 'cafe', etc
            music_type VARCHAR(50),   -- 'none', 'instrumental', 'binaural', etc
            noise_level VARCHAR(20),  -- 'quiet', 'moderate', 'noisy'
            
            -- Session type
            session_type VARCHAR(20) DEFAULT 'pomodoro',  -- 'pomodoro', 'deep_work', 'break', 'meeting'
            break_type VARCHAR(20),   -- 'short', 'long', 'lunch' (se for break)
            
            -- Notes and reflection
            pre_session_notes TEXT,   -- Como está se sentindo antes
            post_session_notes TEXT,  -- Reflexão pós-sessão
            productivity_rating INTEGER CHECK(productivity_rating BETWEEN 1 AND 10),
            
            -- Technical data
            device_type VARCHAR(20),  -- 'desktop', 'mobile', 'tablet'
            app_version VARCHAR(20),
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de configurações do timer
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timer_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_identifier VARCHAR(50) NOT NULL,
            setting_key VARCHAR(100) NOT NULL,
            setting_value TEXT,
            
            -- Meta-settings
            category VARCHAR(50),  -- 'pomodoro', 'tdah', 'notifications', etc
            is_default BOOLEAN DEFAULT FALSE,
            
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(user_identifier, setting_key)
        )
    """)
    
    # Tabela de goals diários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_identifier VARCHAR(50) NOT NULL,
            goal_date DATE NOT NULL,
            
            -- Goal metrics
            target_pomodoros INTEGER DEFAULT 8,
            target_focus_time_minutes INTEGER DEFAULT 240,  -- 4 horas
            target_tasks INTEGER DEFAULT 3,
            
            -- Actual metrics (calculated)
            actual_pomodoros INTEGER DEFAULT 0,
            actual_focus_time_minutes INTEGER DEFAULT 0,
            actual_tasks INTEGER DEFAULT 0,
            
            -- Qualitative goals
            energy_goal VARCHAR(100),
            focus_goal VARCHAR(100),
            
            -- Achievement
            goal_achieved BOOLEAN DEFAULT FALSE,
            achievement_notes TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(user_identifier, goal_date)
        )
    """)
    
    # Índices para performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_task_ref ON timer_sessions(task_reference)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON timer_sessions(user_identifier, DATE(started_at))")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_user_date ON daily_goals(user_identifier, goal_date)")
    
    # Insere configurações padrão
    default_settings = [
        ('dev_user', 'pomodoro_duration', '25', 'pomodoro'),
        ('dev_user', 'short_break_duration', '5', 'pomodoro'),
        ('dev_user', 'long_break_duration', '15', 'pomodoro'),
        ('dev_user', 'auto_start_breaks', 'true', 'pomodoro'),
        ('dev_user', 'notification_sound', 'gentle_chime', 'notifications'),
        ('dev_user', 'focus_reminder_interval', '10', 'tdah'),
        ('dev_user', 'preferred_environment', 'home', 'environment'),
        ('dev_user', 'default_music_type', 'instrumental', 'environment')
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO timer_settings 
        (user_identifier, setting_key, setting_value, category)
        VALUES (?, ?, ?, ?)
    """, default_settings)
    
    # Cria sessões de exemplo baseadas nos tasks migrados
    print("  📊 Criando sessões de exemplo...")
    
    # Busca tasks do framework.db para criar sessões realistas
    framework_conn = sqlite3.connect('framework.db')
    framework_cursor = framework_conn.cursor()
    
    framework_cursor.execute("""
        SELECT t.task_key, t.title, t.estimate_minutes, t.status
        FROM framework_tasks t
        JOIN framework_epics e ON t.epic_id = e.id
        ORDER BY t.id
    """)
    
    tasks = framework_cursor.fetchall()
    framework_conn.close()
    
    # Cria sessões para as últimas 2 semanas
    base_date = datetime.now() - timedelta(days=14)
    sessions_created = 0
    
    for day_offset in range(14):
        current_date = base_date + timedelta(days=day_offset)
        
        # Skip weekends ocasionalmente
        if current_date.weekday() >= 5 and random.random() < 0.7:
            continue
        
        # 2-4 sessões por dia
        daily_sessions = random.randint(2, 4)
        
        for session_num in range(daily_sessions):
            if not tasks:
                continue
                
            task = random.choice(tasks)
            task_ref = f"{task[0]}"  # task_key
            
            # Horário da sessão (9h-18h)
            hour = random.randint(9, 17)
            minute = random.randint(0, 59)
            session_start = current_date.replace(hour=hour, minute=minute, second=0)
            
            # Duração baseada na estimativa da task
            planned_duration = min(random.choice([25, 45, 90]), task[2] or 25)
            actual_duration = planned_duration + random.randint(-5, 15)
            actual_duration = max(10, actual_duration)  # Mínimo 10 minutos
            
            session_end = session_start + timedelta(minutes=actual_duration)
            
            # Métricas TDAH realistas
            focus_rating = random.randint(6, 9)  # Geralmente boa
            energy_level = random.randint(5, 8)
            mood_rating = random.randint(6, 9)
            interruptions = random.randint(0, 3)
            
            # Context
            environments = ['home', 'office', 'cafe', 'library']
            music_types = ['none', 'instrumental', 'binaural', 'nature_sounds', 'lo_fi']
            session_types = ['pomodoro', 'deep_work', 'quick_task']
            
            environment = random.choice(environments)
            music_type = random.choice(music_types)
            session_type = random.choice(session_types)
            
            # Produtividade baseada no foco e interrupções
            productivity = max(1, focus_rating - interruptions)
            
            # Notas realistas
            pre_notes = random.choice([
                "Sentindo-me focado e energizado",
                "Meio disperso, mas vou tentar",
                "Ótimo estado mental para trabalhar",
                "Precisando de cafeína primeiro",
                None
            ])
            
            post_notes = random.choice([
                "Boa sessão, consegui avançar bem",
                "Algumas interrupções, mas produtivo",
                "Fluxo excelente, perdi a noção do tempo",
                "Difícil se concentrar hoje",
                None
            ])
            
            session_data = (
                task_ref, 'dev_user',
                session_start.isoformat(), session_end.isoformat(),
                planned_duration, actual_duration,
                focus_rating, energy_level, mood_rating, interruptions,
                environment, music_type, 'quiet',
                session_type, None,
                pre_notes, post_notes, productivity,
                'desktop', '1.0.0'
            )
            
            cursor.execute("""
                INSERT INTO timer_sessions (
                    task_reference, user_identifier,
                    started_at, ended_at,
                    planned_duration_minutes, actual_duration_minutes,
                    focus_rating, energy_level, mood_rating, interruptions_count,
                    environment, music_type, noise_level,
                    session_type, break_type,
                    pre_session_notes, post_session_notes, productivity_rating,
                    device_type, app_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, session_data)
            
            sessions_created += 1
    
    # Cria goals diários para última semana
    for day_offset in range(7):
        goal_date = (datetime.now() - timedelta(days=day_offset)).date()
        
        # Goals realistas
        target_pomodoros = random.randint(6, 10)
        target_focus_time = target_pomodoros * 25  # Aproximado
        target_tasks = random.randint(2, 4)
        
        # Calcula actual baseado nas sessões do dia
        cursor.execute("""
            SELECT 
                COUNT(*) as session_count,
                SUM(actual_duration_minutes) as total_time,
                COUNT(DISTINCT task_reference) as unique_tasks
            FROM timer_sessions 
            WHERE user_identifier = 'dev_user' 
            AND DATE(started_at) = ?
        """, (goal_date.isoformat(),))
        
        actual_data = cursor.fetchone()
        actual_pomodoros = actual_data[0] if actual_data[0] else 0
        actual_time = actual_data[1] if actual_data[1] else 0
        actual_tasks = actual_data[2] if actual_data[2] else 0
        
        goal_achieved = (
            actual_pomodoros >= target_pomodoros * 0.8 and
            actual_time >= target_focus_time * 0.8
        )
        
        cursor.execute("""
            INSERT OR REPLACE INTO daily_goals (
                user_identifier, goal_date,
                target_pomodoros, target_focus_time_minutes, target_tasks,
                actual_pomodoros, actual_focus_time_minutes, actual_tasks,
                energy_goal, focus_goal, goal_achieved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'dev_user', goal_date,
            target_pomodoros, target_focus_time, target_tasks,
            actual_pomodoros, actual_time, actual_tasks,
            'Manter energia constante ao longo do dia',
            'Minimizar interrupções e manter foco profundo',
            goal_achieved
        ))
    
    conn.commit()
    conn.close()
    
    print(f"  ✅ {sessions_created} sessões de timer criadas")
    print(f"  ✅ 7 goals diários configurados")
    print(f"  ✅ 8 configurações padrão inseridas")
    
    return sessions_created

def test_task_timer_integration():
    """Testa integração entre task_timer.db e framework.db."""
    print("\n🔗 Testando integração task_timer ↔ framework...")
    
    # Conecta aos dois bancos
    timer_conn = sqlite3.connect('task_timer.db')
    framework_conn = sqlite3.connect('framework.db')
    
    timer_cursor = timer_conn.cursor()
    framework_cursor = framework_conn.cursor()
    
    # Query de integração: sessões por task
    integration_query = """
        SELECT 
            ts.task_reference,
            COUNT(*) as session_count,
            SUM(ts.actual_duration_minutes) as total_time,
            AVG(ts.focus_rating) as avg_focus,
            AVG(ts.productivity_rating) as avg_productivity
        FROM timer_sessions ts
        WHERE ts.user_identifier = 'dev_user'
        GROUP BY ts.task_reference
        ORDER BY total_time DESC
    """
    
    timer_cursor.execute(integration_query)
    timer_stats = timer_cursor.fetchall()
    
    print("  📊 Estatísticas de integração:")
    for stat in timer_stats:
        task_ref, sessions, total_time, avg_focus, avg_prod = stat
        
        # Busca info da task no framework.db
        framework_cursor.execute("""
            SELECT t.title, e.name 
            FROM framework_tasks t
            JOIN framework_epics e ON t.epic_id = e.id
            WHERE t.task_key = ?
        """, (task_ref,))
        
        task_info = framework_cursor.fetchone()
        if task_info:
            print(f"    🎯 {task_ref}: {task_info[0]}")
            print(f"       📈 {sessions} sessões, {total_time}min total")
            print(f"       🎯 Foco: {avg_focus:.1f}/10, Produtividade: {avg_prod:.1f}/10")
    
    timer_conn.close()
    framework_conn.close()
    
    print("  ✅ Integração funcionando corretamente")

def main():
    """Cria task_timer.db stub completo."""
    print("⏰ CRIANDO TASK_TIMER.DB STUB")
    print("=" * 50)
    
    sessions_count = create_task_timer_db()
    test_task_timer_integration()
    
    print(f"\n✅ task_timer.db criado com sucesso")
    print(f"📊 Total: {sessions_count} sessões + configurações + goals")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)