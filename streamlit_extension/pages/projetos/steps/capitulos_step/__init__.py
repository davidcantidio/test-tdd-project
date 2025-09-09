"""Módulo Capítulos - Segunda macro etapa do wizard genérico.

Este módulo implementa a gestão de Capítulos (épicos) no framework
universal de projetos. Capítulos representam as grandes divisões
de um projeto, aplicável a qualquer domínio (construção, software,
conteúdo, educação, etc.).

Architecture:
    - main.py: Interface principal com formulário vertical
    - form_mode.py: Modo formulário completo
    - summary.py: Resumo e listagem dos capítulos
    - ai_refine.py: Refinamento por IA (futuro)
"""

from .main import render_capitulos_step
from .epic_review import EpicReviewPage, render_epic_review_step, should_show_epic_review_step, is_review_complete

__all__ = ['render_capitulos_step', 'EpicReviewPage', 'render_epic_review_step', 'should_show_epic_review_step', 'is_review_complete']