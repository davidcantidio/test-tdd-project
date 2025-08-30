# tests/test_product_vision_step_exports.py
def test_module_exports():
    import importlib
    m = importlib.import_module(
        "streamlit_extension.pages.projetos.steps.product_vision_step"
    )
    for name in ["render_product_vision_with_toggle", "render_step", "validate", "get_summary"]:
        assert hasattr(m, name), f"missing export: {name}"
