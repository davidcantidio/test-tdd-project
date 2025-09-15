"""Infrastructure Adapters - Framework Interfaces

Adapters that connect the core to external frameworks and systems.

Future adapters (História 3.1):
    - StreamlitAdapter: Streamlit UI integration
    - FastAPIAdapter: REST API integration (Marco 1)
    - CLIAdapter: Command-line interface (Marco 1)
    - SessionStateAdapter: Session management

Status: História 1.1 Complete - Structure Ready
Next: História 3.1 - StreamlitAdapter Creation
"""

from .relations_adapter import (
    get_epics_for_product_vision,
    get_user_stories_for_epic,
    get_tasks_for_user_story,
)

__all__: list[str] = [
    "get_epics_for_product_vision",
    "get_user_stories_for_epic",
    "get_tasks_for_user_story",
]
