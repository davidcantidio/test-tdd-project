"""Módulo Capítulos - Segunda macro etapa do wizard genérico.

Implementa a gestão de Capítulos (épicos), as grandes divisões do projeto,
aplicável a qualquer domínio (construção, software, conteúdo, educação, etc.).

Arquitetura (atual):
    - capitulos.py: Interface principal com formulário vertical
    - form_mode.py: Utilidades do modo formulário (quando aplicável)
    - epic_review.py: Tela de revisão e análise dos capítulos
"""

from .capitulos import render_capitulos_step
from .epic_review import EpicReviewPage, render_epic_review_step, should_show_epic_review_step, is_review_complete

__all__ = ['render_capitulos_step', 'EpicReviewPage', 'render_epic_review_step', 'should_show_epic_review_step', 'is_review_complete']
