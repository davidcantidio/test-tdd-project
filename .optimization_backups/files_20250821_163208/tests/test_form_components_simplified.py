"""
🧪 Tests for Simplified DRY Form Components

Tests for the refactored form system covering:
- StandardForm base functionality  
- ClientForm specialized validation
- ProjectForm specialized validation
- Form validation integration
- Security integration
"""

import types
import sys
import pytest

# Mock psutil to avoid import issues in tests
sys.modules.setdefault("psutil", types.SimpleNamespace())

from streamlit_extension.components.form_components import (
    StandardForm, ClientForm, ProjectForm,
    create_client_form, create_project_form,
    render_success_message, render_error_messages
)
from streamlit_extension.utils import form_validation as fv


class DummyStreamlit:
    """Mock Streamlit for testing without actual UI."""
    
    def __init__(self, inputs=None):
        self.inputs = inputs or {}
        self.errors = []
        self.successes = []

    def text_input(self, label, key=None, placeholder=None, help=None):
        return self.inputs.get(key, "")

    def text_area(self, label, key=None, placeholder=None, help=None):
        return self.inputs.get(key, "")

    def selectbox(self, label, options, key=None, help=None):
        return self.inputs.get(key, options[0] if options else None)

    def number_input(self, label, min_value=0.0, max_value=None, step=1.0, key=None, help=None):
        return self.inputs.get(key, min_value)

    def checkbox(self, label, value=False, key=None, help=None):
        return self.inputs.get(key, value)

    def form_submit_button(self, label):
        return True

    def error(self, msg):
        self.errors.append(msg)

    def success(self, msg):
        self.successes.append(msg)

    def form(self, form_id):
        class MockForm:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return None
        return MockForm()

    def markdown(self, text):
        pass

    def modal(self, title, width="large"):
        class MockModal:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return None
        return MockModal()

    def expander(self, title, expanded=False):
        class MockExpander:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return None
        return MockExpander()


# ------------------------------------------------------------------
# StandardForm Tests

def test_standard_form_initialization():
    """Test StandardForm basic initialization."""
    st = DummyStreamlit()
    form = StandardForm("test_form", "Test Title", st_module=st)
    
    assert form.form_id == "test_form"
    assert form.title == "Test Title"
    assert form.get_form_data() == {}
    assert form.errors == []
    assert form.submitted == False


def test_standard_form_text_input():
    """Test text input rendering and data collection."""
    st = DummyStreamlit({"test_form_name": "Test Value"})
    form = StandardForm("test_form", "Test Title", st_module=st)
    
    value = form.render_text_input("Name", "name", placeholder="Enter name")
    
    assert value == "Test Value"
    assert form.get_form_data()["name"] == "Test Value"


def test_standard_form_selectbox():
    """Test selectbox rendering and data collection."""
    st = DummyStreamlit({"test_form_status": "active"})
    form = StandardForm("test_form", "Test Title", st_module=st)
    
    value = form.render_select_box("Status", "status", ["active", "inactive"])
    
    assert value == "active"
    assert form.get_form_data()["status"] == "active"


def test_standard_form_number_input():
    """Test number input rendering with validation."""
    st = DummyStreamlit({"test_form_budget": 1000.0})
    form = StandardForm("test_form", "Test Title", st_module=st)
    
    value = form.render_number_input("Budget", "budget", min_value=0.0, step=100.0)
    
    assert value == 1000.0
    assert form.get_form_data()["budget"] == 1000.0


def test_standard_form_checkbox():
    """Test checkbox rendering."""
    st = DummyStreamlit({"test_form_active": True})
    form = StandardForm("test_form", "Test Title", st_module=st)
    
    value = form.render_checkbox("Active", "active", value=False)
    
    assert value == True
    assert form.get_form_data()["active"] == True


def test_standard_form_submit_button():
    """Test submit button rendering."""
    st = DummyStreamlit()
    form = StandardForm("test_form", "Test Title", st_module=st)
    
    submitted = form.render_submit_button("Save")
    
    assert submitted == True
    assert form.submitted == True


# TODO: Consider extracting this block into a separate method
def test_standard_form_validation():
    """Test form validation integration."""
    st = DummyStreamlit()
    form = StandardForm("test_form", "Test Title", st_module=st)
    
    # Test successful validation
    valid_data = {"name": "Test", "email": "test@example.com"}
    success, errors = form.validate_and_submit(valid_data, lambda data: [])
    assert success == True
    assert errors == []
    
    # Test failed validation
    invalid_data = {"name": "", "email": "invalid"}
    success, errors = form.validate_and_submit(invalid_data, lambda data: ["Name is required"])
    assert success == False
    assert "Name is required" in errors


def test_standard_form_modal_context():
    """Test modal form context manager."""
    st = DummyStreamlit()
    form = StandardForm("test_form", "Test Title", st_module=st)
    
    # Should not raise an exception
    with form.modal_form():
        form.render_text_input("Test", "test")


def test_standard_form_expander_context():
    """Test expander form context manager."""
    st = DummyStreamlit()
    form = StandardForm("test_form", "Test Title", st_module=st)
    
    # Should not raise an exception
    with form.expander_form():
        form.render_text_input("Test", "test")


# ------------------------------------------------------------------
# ClientForm Tests

def test_client_form_initialization():
    """Test ClientForm initialization."""
    form = ClientForm("client_form", "Create Client")
    
    assert form.form_id == "client_form"
    assert form.title == "Create Client"
    assert isinstance(form, StandardForm)


# TODO: Consider extracting this block into a separate method

def test_client_form_validation_success():
    """Test successful client validation."""
    form = ClientForm("client_form", "Create Client")
    
    valid_data = {
        "client_key": "test_client",
        "name": "Test Client",
        "primary_contact_email": "test@example.com",
        "primary_contact_phone": "+55 11 99999-9999"
    }
    
    errors = form.validate_client_data(valid_data)
    # TODO: Consider extracting this block into a separate method
    assert errors == []


def test_client_form_validation_missing_required():
    """Test client validation with missing required fields."""
    form = ClientForm("client_form", "Create Client")
    
    invalid_data = {
        "client_key": "",
        "name": "",
        "primary_contact_email": ""
    }
    
    errors = form.validate_client_data(invalid_data)
    assert len(errors) > 0
    assert any("Missing required field" in error for error in errors)


def test_client_form_validation_invalid_email():
    """Test client validation with invalid email."""
    form = ClientForm("client_form", "Create Client")
    
    invalid_data = {
        "client_key": "test_client",
        "name": "Test Client", 
        "primary_contact_email": "invalid-email"
    }
    
    # TODO: Consider extracting this block into a separate method
    errors = form.validate_client_data(invalid_data)
    assert any("Invalid email format" in error for error in errors)


def test_client_form_validation_invalid_phone():
    """Test client validation with invalid phone."""
    form = ClientForm("client_form", "Create Client")
    
    invalid_data = {
        "client_key": "test_client",
        "name": "Test Client",
        "primary_contact_email": "test@example.com",
        "primary_contact_phone": "123"  # Too short
    }
    
    errors = form.validate_client_data(invalid_data)
    assert any("Invalid phone format" in error for error in errors)


def test_client_form_render_fields():
    """Test client form field rendering."""
    st = DummyStreamlit()
    form = ClientForm("client_form", "Create Client", st_module=st)
    
    # Should not raise an exception
    result = form.render_client_fields()
    assert result == True


# ------------------------------------------------------------------
# ProjectForm Tests

def test_project_form_initialization():
    """Test ProjectForm initialization."""
    form = ProjectForm("project_form", "Create Project")
    
    # TODO: Consider extracting this block into a separate method
    assert form.form_id == "project_form"
    assert form.title == "Create Project"
    assert isinstance(form, StandardForm)


def test_project_form_validation_success():
    """Test successful project validation."""
    form = ProjectForm("project_form", "Create Project")
    
    valid_data = {
        "client_id": 1,
        "project_key": "test_project",
        "name": "Test Project",
        "status": "planning"
    # TODO: Consider extracting this block into a separate method
    }
    
    errors = form.validate_project_data(valid_data)
    assert errors == []


def test_project_form_validation_missing_required():
    """Test project validation with missing required fields."""
    form = ProjectForm("project_form", "Create Project")
    
    invalid_data = {
        "client_id": "",
        "project_key": "",
        "name": "",
        "status": ""
    # TODO: Consider extracting this block into a separate method
    }
    
    errors = form.validate_project_data(invalid_data)
    assert len(errors) > 0
    assert any("Missing required field" in error for error in errors)


def test_project_form_validation_short_key():
    """Test project validation with short project key."""
    form = ProjectForm("project_form", "Create Project")
    
    invalid_data = {
        "client_id": 1,
        "project_key": "a",  # Too short
        "name": "Test Project",
        "status": "planning"
    }
    
    errors = form.validate_project_data(invalid_data)
    assert any("must be at least" in error for error in errors)


def test_project_form_render_fields():
    """Test project form field rendering."""
    st = DummyStreamlit()
    form = ProjectForm("project_form", "Create Project", st_module=st)
    
    client_options = ["Client 1", "Client 2"]
    
    # Should not raise an exception
    result = form.render_project_fields(client_options)
    assert result == True


# ------------------------------------------------------------------
# Form Validation Module Tests

def test_form_validation_required_fields():
    """Test required field validation."""
    errors = fv.validate_required_fields({"name": "Test"}, ["name", "email"])
    assert "Missing required field: email" in errors


def test_form_validation_email_format():
    """Test email format validation."""
    assert fv.validate_email_format("test@example.com") == True
    assert fv.validate_email_format("invalid-email") == False
    assert fv.validate_email_format("") == False


def test_form_validation_phone_format():
    """Test phone format validation."""
    assert fv.validate_phone_format("+55 11 99999-9999") == True
    assert fv.validate_phone_format("11999999999") == True
    assert fv.validate_phone_format("123") == False
    assert fv.validate_phone_format("") == False


def test_form_validation_text_length():
    """Test text length validation."""
    errors = fv.validate_text_length("ab", 3, 10, "field")
    assert "must be at least 3 characters" in errors[0]
    
# TODO: Consider extracting this block into a separate method
    
    errors = fv.validate_text_length("a" * 11, 3, 10, "field")
    assert "must be at most 10 characters" in errors[0]
    
    errors = fv.validate_text_length("test", 3, 10, "field")
    assert errors == []


def test_form_validation_business_rules():
    """Test business rules validation."""
    # Client rules
    client_errors = fv.validate_business_rules_client({
        "client_key": "a",  # Too short
        "name": ""  # Empty
    })
    assert len(client_errors) > 0
    
    # Project rules
    project_errors = fv.validate_business_rules_project({
        "project_key": "a",  # Too short
        "name": ""  # Empty
    })
    assert len(project_errors) > 0


def test_form_validation_sanitize_inputs():
    """Test input sanitization."""
    data = {
        "name": "Test Name",
        "description": "Test Description",
        "count": 42
    }
    
    sanitized = fv.sanitize_form_inputs(data)
    assert "name" in sanitized
    assert "description" in sanitized
    assert "count" in sanitized
    assert sanitized["count"] == 42  # Non-string should remain unchanged


# ------------------------------------------------------------------
# Convenience Functions Tests

def test_create_client_form():
    """Test client form creation convenience function."""
    form = create_client_form("test_id", "Test Title")
    
    assert isinstance(form, ClientForm)
    assert form.form_id == "test_id"
    assert form.title == "Test Title"


# TODO: Consider extracting this block into a separate method

def test_create_project_form():
    """Test project form creation convenience function."""
    form = create_project_form("test_id", "Test Title")
    
    assert isinstance(form, ProjectForm)
    assert form.form_id == "test_id"
    assert form.title == "Test Title"


def test_render_messages():
    """Test message rendering functions."""
    st = DummyStreamlit()
    
    # Mock the global st variable for the functions
    import streamlit_extension.components.form_components as fc
    original_st = fc.st
    fc.st = st
    
    try:
        render_success_message("Success!")
        assert len(st.successes) == 1
        assert "✅ Success!" in st.successes[0]
        
# TODO: Consider extracting this block into a separate method
        
        render_error_messages(["Error 1", "Error 2"])
        assert len(st.errors) == 2
        assert "❌ Error 1" in st.errors[0]
        assert "❌ Error 2" in st.errors[1]
    finally:
        fc.st = original_st


# ------------------------------------------------------------------
# Integration Tests

def test_full_client_form_workflow():
    """Test complete client form workflow."""
    st = DummyStreamlit({
        "client_form_client_key": "test_client",
        "client_form_name": "Test Client",
        "client_form_primary_contact_email": "test@example.com",
        "client_form_status": "active"
    })
    
    form = ClientForm("client_form", "Create Client", st_module=st)
    
# TODO: Consider extracting this block into a separate method
    
    # Render form (should collect data)
    form.render_client_fields()
    
    # Get and validate data
    data = form.get_form_data()
    errors = form.validate_client_data(data)
    
    assert data["client_key"] == "test_client"
    assert data["name"] == "Test Client"
    assert data["primary_contact_email"] == "test@example.com"
    assert errors == []


def test_full_project_form_workflow():
    """Test complete project form workflow."""
    st = DummyStreamlit({
        "project_form_client_id": "Client 1",
        "project_form_project_key": "test_project",
        "project_form_name": "Test Project",
        "project_form_status": "planning",
        "project_form_budget": 5000.0
    })
    
    form = ProjectForm("project_form", "Create Project", st_module=st)
    
    # Render form (should collect data)
    form.render_project_fields(["Client 1", "Client 2"])
    
    # Get and validate data
    data = form.get_form_data()
    errors = form.validate_project_data(data)
    
    assert data["client_id"] == "Client 1"
    assert data["project_key"] == "test_project"
    assert data["name"] == "Test Project"
    assert data["budget"] == 5000.0
    assert errors == []


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])