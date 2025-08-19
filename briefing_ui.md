"""
Objetivo:
Refatorar o módulo atual `render_sidebar` que contém cerca de 600 linhas de código
e dividi-lo em uma estrutura modular mais limpa, legível e testável.

🏗️ Estrutura proposta de pastas e arquivos (criar ou mover conforme necessário):

streamlit_extension/
└── components/
    └── sidebar/
        ├── __init__.py
        ├── layout.py             # render_sidebar() e render_timer_controls()
        ├── timer.py              # start_timer(), pause_timer(), stop_timer(), get_elapsed_time()
        ├── gamification.py       # _get_gamification_data(), _get_next_achievement_progress(), _get_achievement_emoji()
        ├── streaks.py            # _calculate_streaks()
        ├── points.py             # _calculate_recent_points()
        ├── fallback.py           # _get_fallback_gamification_data()
        └── database_utils.py     # get_connection_context (se necessário para Focus Time)

📌 Ações:

1. Mover as funções auxiliares relacionadas a timer para `timer.py`.
   Ex: start_timer, pause_timer, stop_timer, get_elapsed_time

2. Mover funções que processam conquistas e gamificação para `gamification.py`.

3. Mover o cálculo de streaks para `streaks.py`.

4. Mover cálculo de pontuação recente para `points.py`.

5. Mover dados fallback simulados de gamificação para `fallback.py`.

6. A função principal `render_sidebar()` e `render_timer_controls()` permanecem em `layout.py`,
   importando todas as funções auxiliares dos demais arquivos.

7. Garantir que `__init__.py` exponha `render_sidebar` como função pública do pacote.

8. Garantir que todos os imports relativos (`..config`, `..database`, etc.) continuem funcionando
   e que o módulo `sidebar` possa ser usado via:
   `from streamlit_extension.components.sidebar import render_sidebar`

9. Nenhuma funcionalidade deve ser perdida. O comportamento atual deve ser preservado.

10. Adicionar comentários simples nos arquivos novos indicando a função de cada um.

"""
