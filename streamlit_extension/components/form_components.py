#!/usr/bin/env python3
"""
🏗️ DRY Form Components

Addresses report.md requirement: "Refactor repeated form logic into DRY components"

This module provides reusable form components that eliminate code duplication:
- StandardForm: Modal and expander form patterns
- InputSection: Common input groupings
- FormValidator: Centralized validation logic
- SecurityForm: CSRF token handling
- SubmissionHandler: Form submission patterns
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple, Union
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

try:
    from streamlit_extension.utils.security import security_manager, validate_form
    from streamlit_extension.utils.validators import validate_client_data, validate_project_data
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    security_manager = validate_form = None
    validate_client_data = validate_project_data = None


@dataclass
class FormConfig:
    """Configuration for form components."""
    form_id: str
    title: str
    submit_text: str = "Submit"
    cancel_text: str = "Cancel"
    enable_csrf: bool = True
    enable_rate_limit: bool = True
    columns: int = 2
    submit_button_type: str = "primary"
    clear_on_submit: bool = False


@dataclass
class InputField:
    """Configuration for individual input fields."""
    name: str
    label: str
    input_type: str = "text_input"
    required: bool = False
    placeholder: str = ""
    value: Any = None
    help_text: str = ""
    options: List[Any] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    validation_func: Optional[Callable] = None


class FormValidator:
    """Centralized form validation logic."""
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate that required fields are present and non-empty."""
        errors = []
        for field in required_fields:
            if not data.get(field):
                errors.append(f"{field.replace('_', ' ').title()} is required")
        return errors
    
    @staticmethod
    def validate_email(email: str) -> Optional[str]:
        """Validate email format."""
        if not email:
            return None
        
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return "Invalid email format"
        return None
    
    @staticmethod
    def validate_phone(phone: str) -> Optional[str]:
        """Validate phone number format."""
        if not phone:
            return None
        
        import re
        # Remove non-digit characters for validation
        digits_only = re.sub(r'[^\d]', '', phone)
        if len(digits_only) < 10 or len(digits_only) > 15:
            return "Phone number must be between 10-15 digits"
        return None
    
    @staticmethod
    def validate_unique_key(key: str, existing_keys: List[str]) -> Optional[str]:
        """Validate that a key is unique."""
        if key in existing_keys:
            return f"Key '{key}' already exists"
        return None


class SecurityForm:
    """Handles security aspects of forms."""
    
    @staticmethod
    def generate_csrf_token(form_id: str) -> Optional[str]:
        """Generate CSRF token for form."""
        if SECURITY_AVAILABLE and security_manager:
            return security_manager.get_csrf_form_field(form_id)
        return None
    
    @staticmethod
    def validate_csrf_token(form_id: str, token: str) -> bool:
        """Validate CSRF token."""
        if SECURITY_AVAILABLE and security_manager:
            return security_manager.validate_csrf_token(form_id, token)
        return True  # Pass through if security not available
    
    @staticmethod
    def check_rate_limit(user_id: str = "anonymous") -> bool:
        """Check rate limiting."""
        if SECURITY_AVAILABLE and hasattr(security_manager, 'check_rate_limit'):
            return security_manager.check_rate_limit(user_id)
        return True  # Pass through if rate limiting not available


class InputRenderer:
    """Renders different types of input fields."""
    
    @staticmethod
    def render_field(field: InputField, column=None) -> Any:
        """Render an input field based on its configuration."""
        if not STREAMLIT_AVAILABLE:
            return None
        
        # Determine where to render (column or main area)
        render_ctx = column if column else st
        
        # Common parameters
        kwargs = {
            "key": field.name,
            "help": field.help_text if field.help_text else None,
            "placeholder": field.placeholder if field.placeholder else None
        }
        
        # Add value if provided
        if field.value is not None:
            kwargs["value"] = field.value
        
        # Add type-specific parameters
        if field.input_type in ["number_input"]:
            if field.min_value is not None:
                kwargs["min_value"] = field.min_value
            if field.max_value is not None:
                kwargs["max_value"] = field.max_value
            if field.step is not None:
                kwargs["step"] = field.step
        
        # Render based on type
        if field.input_type == "text_input":
            return render_ctx.text_input(field.label, **kwargs)
        elif field.input_type == "text_area":
            return render_ctx.text_area(field.label, **kwargs)
        elif field.input_type == "number_input":
            return render_ctx.number_input(field.label, **kwargs)
        elif field.input_type == "selectbox":
            return render_ctx.selectbox(field.label, options=field.options or [], **kwargs)
        elif field.input_type == "multiselect":
            return render_ctx.multiselect(field.label, options=field.options or [], **kwargs)
        elif field.input_type == "checkbox":
            checked = kwargs.get("value", False)
            return render_ctx.checkbox(field.label, value=checked, key=field.name, help=field.help_text)
        elif field.input_type == "date_input":
            return render_ctx.date_input(field.label, **kwargs)
        elif field.input_type == "email":
            return render_ctx.text_input(field.label, **kwargs)
        elif field.input_type == "password":
            return render_ctx.text_input(field.label, type="password", **kwargs)
        else:
            # Fallback to text input
            return render_ctx.text_input(field.label, **kwargs)


class StandardForm:
    """Reusable form component that handles common patterns."""
    
    def __init__(self, config: FormConfig):
        self.config = config
        self.validator = FormValidator()
        self.security = SecurityForm()
        self.renderer = InputRenderer()
        self.csrf_token = None
        
    @contextmanager
    def modal_form(self, width: str = "large"):
        """Context manager for modal forms."""
        if not STREAMLIT_AVAILABLE:
            yield
            return
            
        with st.modal(self.config.title, width=width):
            with st.form(self.config.form_id):
                # Generate CSRF token
                if self.config.enable_csrf:
                    self.csrf_token = self.security.generate_csrf_token(self.config.form_id)
                
                yield
    
    @contextmanager
    def expander_form(self, expanded: bool = False):
        """Context manager for expander forms."""
        if not STREAMLIT_AVAILABLE:
            yield
            return
            
        with st.expander(self.config.title, expanded=expanded):
            with st.form(self.config.form_id):
                # Generate CSRF token
                if self.config.enable_csrf:
                    self.csrf_token = self.security.generate_csrf_token(self.config.form_id)
                
                yield
    
    @contextmanager
    def form_layout(self):
        """Create standardized form layout with columns."""
        if not STREAMLIT_AVAILABLE:
            yield None
            return
            
        if self.config.columns > 1:
            columns = st.columns(self.config.columns)
            yield columns
        else:
            yield None
    
    def render_title(self, subtitle: str = None):
        """Render form title and subtitle."""
        if not STREAMLIT_AVAILABLE:
            return
            
        st.markdown(f"### {self.config.title}")
        if subtitle:
            st.markdown(f"*{subtitle}*")
    
    def render_section(self, title: str, fields: List[InputField], column=None) -> Dict[str, Any]:
        """Render a section of form fields."""
        if not STREAMLIT_AVAILABLE:
            return {}
            
        # Determine render context
        ctx = column if column else st
        
        # Section header
        ctx.markdown(f"#### {title}")
        
        # Render fields and collect values
        values = {}
        for field in fields:
            values[field.name] = self.renderer.render_field(field, column)
        
        return values
    
    def render_submit_buttons(self) -> Tuple[bool, bool]:
        """Render submit and cancel buttons."""
        if not STREAMLIT_AVAILABLE:
            return False, False
            
        col1, col2 = st.columns([1, 1])
        
        with col1:
            submitted = st.form_submit_button(
                self.config.submit_text,
                type=self.config.submit_button_type,
                use_container_width=True
            )
        
        with col2:
            cancelled = st.form_submit_button(
                self.config.cancel_text,
                use_container_width=True
            )
        
        return submitted, cancelled
    
    def validate_and_submit(self, 
                          data: Dict[str, Any], 
                          required_fields: List[str],
                          validation_func: Optional[Callable] = None,
                          submit_func: Optional[Callable] = None) -> Dict[str, Any]:
        """Validate form data and handle submission."""
        result = {
            "success": False,
            "errors": [],
            "data": data
        }
        
        # Check rate limiting
        if self.config.enable_rate_limit:
            if not self.security.check_rate_limit():
                result["errors"].append("Rate limit exceeded. Please try again later.")
                return result
        
        # Validate CSRF token
        if self.config.enable_csrf and self.csrf_token:
            if not self.security.validate_csrf_token(self.config.form_id, self.csrf_token):
                result["errors"].append("Security validation failed.")
                return result
        
        # Validate required fields
        field_errors = self.validator.validate_required_fields(data, required_fields)
        result["errors"].extend(field_errors)
        
        # Custom validation
        if validation_func:
            custom_errors = validation_func(data)
            if custom_errors:
                result["errors"].extend(custom_errors)
        
        # If no errors, submit
        if not result["errors"] and submit_func:
            try:
                submit_result = submit_func(data)
                if submit_result:
                    result["success"] = True
                else:
                    result["errors"].append("Submission failed")
            except Exception as e:
                result["errors"].append(f"Error during submission: {str(e)}")
        
        return result


class ClientForm(StandardForm):
    """Specialized form for client management."""
    
    def get_client_fields(self, client_data: Dict[str, Any] = None) -> Tuple[List[InputField], List[InputField]]:
        """Get client form fields organized by section."""
        basic_fields = [
            InputField("client_key", "Client Key*", required=True, 
                      value=client_data.get("client_key", "") if client_data else "",
                      placeholder="e.g., client_xyz"),
            InputField("name", "Client Name*", required=True,
                      value=client_data.get("name", "") if client_data else "",
                      placeholder="e.g., Company ABC"),
            InputField("description", "Description", input_type="text_area",
                      value=client_data.get("description", "") if client_data else "",
                      placeholder="Brief description of the client..."),
            InputField("industry", "Industry",
                      value=client_data.get("industry", "") if client_data else "",
                      placeholder="e.g., Technology")
        ]
        
        contact_fields = [
            InputField("contact_name", "Contact Name",
                      value=client_data.get("contact_name", "") if client_data else "",
                      placeholder="Primary contact person"),
            InputField("contact_email", "Contact Email", input_type="email",
                      value=client_data.get("contact_email", "") if client_data else "",
                      placeholder="contact@company.com"),
            InputField("contact_phone", "Contact Phone",
                      value=client_data.get("contact_phone", "") if client_data else "",
                      placeholder="+1 (555) 123-4567"),
            InputField("status", "Status", input_type="selectbox",
                      options=["active", "inactive", "suspended", "archived"],
                      value=client_data.get("status", "active") if client_data else "active")
        ]
        
        return basic_fields, contact_fields
    
    def validate_client_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate client-specific data."""
        errors = []
        
        # Email validation
        if data.get("contact_email"):
            email_error = self.validator.validate_email(data["contact_email"])
            if email_error:
                errors.append(email_error)
        
        # Phone validation
        if data.get("contact_phone"):
            phone_error = self.validator.validate_phone(data["contact_phone"])
            if phone_error:
                errors.append(phone_error)
        
        # Use existing validation if available
        if SECURITY_AVAILABLE and validate_client_data:
            try:
                external_errors = validate_client_data(data)
                if external_errors:
                    errors.extend(external_errors)
            except Exception:
                pass  # Fallback gracefully
        
        return errors


class ProjectForm(StandardForm):
    """Specialized form for project management."""
    
    def get_project_fields(self, project_data: Dict[str, Any] = None, clients_map: Dict[int, str] = None) -> Tuple[List[InputField], List[InputField]]:
        """Get project form fields organized by section."""
        basic_fields = [
            InputField("name", "Project Name*", required=True,
                      value=project_data.get("name", "") if project_data else "",
                      placeholder="e.g., Website Redesign"),
            InputField("description", "Description", input_type="text_area",
                      value=project_data.get("description", "") if project_data else "",
                      placeholder="Project details and objectives..."),
            InputField("status", "Status", input_type="selectbox",
                      options=["planning", "active", "on_hold", "completed", "cancelled"],
                      value=project_data.get("status", "planning") if project_data else "planning"),
            InputField("priority", "Priority", input_type="selectbox",
                      options=["low", "medium", "high", "critical"],
                      value=project_data.get("priority", "medium") if project_data else "medium")
        ]
        
        # Add client selection field
        if clients_map:
            client_options = list(clients_map.values())
            current_value = None
            if project_data and project_data.get("client_id"):
                current_value = clients_map.get(project_data["client_id"])
            
            basic_fields.insert(0, InputField(
                "client_id", "Client*", input_type="selectbox", required=True,
                options=client_options, value=current_value
            ))
        
        timeline_fields = [
            InputField("start_date", "Start Date", input_type="date_input",
                      value=project_data.get("start_date") if project_data else None),
            InputField("end_date", "End Date", input_type="date_input",
                      value=project_data.get("end_date") if project_data else None),
            InputField("budget", "Budget", input_type="number_input",
                      value=project_data.get("budget") if project_data else None,
                      min_value=0.0, step=100.0),
            InputField("estimated_hours", "Estimated Hours", input_type="number_input",
                      value=project_data.get("estimated_hours") if project_data else None,
                      min_value=0.0, step=1.0)
        ]
        
        return basic_fields, timeline_fields
    
    def validate_project_data(self, data: Dict[str, Any], clients_map: Dict[int, str] = None) -> List[str]:
        """Validate project-specific data."""
        errors = []
        
        # Client validation
        if clients_map and data.get("client_id"):
            # Convert client name back to ID
            client_name = data["client_id"]
            client_id = None
            for cid, cname in clients_map.items():
                if cname == client_name:
                    client_id = cid
                    break
            
            if client_id is None:
                errors.append("Invalid client selection")
            else:
                data["client_id"] = client_id  # Convert back to ID for processing
        
        # Date validation
        if data.get("start_date") and data.get("end_date"):
            if data["start_date"] > data["end_date"]:
                errors.append("End date must be after start date")
        
        # Use existing validation if available
        if SECURITY_AVAILABLE and validate_project_data:
            try:
                external_errors = validate_project_data(data)
                if external_errors:
                    errors.extend(external_errors)
            except Exception:
                pass  # Fallback gracefully
        
        return errors


# Convenience functions for common form patterns
def create_client_form(form_id: str, title: str, modal: bool = True) -> ClientForm:
    """Create a client form with standard configuration."""
    config = FormConfig(
        form_id=form_id,
        title=title,
        submit_text="Save Client",
        cancel_text="Cancel"
    )
    return ClientForm(config)


def create_project_form(form_id: str, title: str, modal: bool = True) -> ProjectForm:
    """Create a project form with standard configuration."""
    config = FormConfig(
        form_id=form_id,
        title=title,
        submit_text="Save Project",
        cancel_text="Cancel"
    )
    return ProjectForm(config)


def render_success_message(message: str, icon: str = "✅"):
    """Render a standardized success message."""
    if STREAMLIT_AVAILABLE:
        st.success(f"{icon} {message}")


def render_error_messages(errors: List[str], icon: str = "❌"):
    """Render standardized error messages."""
    if STREAMLIT_AVAILABLE and errors:
        for error in errors:
            st.error(f"{icon} {error}")


# Backwards compatibility exports
ValidatedInput = InputField
ConfigurationForm = StandardForm
ButtonGroup = StandardForm  # Placeholder - buttons are handled in StandardForm


if __name__ == "__main__":
    # Test form components
    print("🏗️ Testing DRY Form Components")
    print("=" * 50)
    
    # Test form configuration
    config = FormConfig(
        form_id="test_form",
        title="Test Form",
        submit_text="Submit Test"
    )
    
    # Test input field configuration
    field = InputField(
        name="test_field",
        label="Test Field",
        input_type="text_input",
        required=True,
        placeholder="Enter test value"
    )
    
    print("✅ Form components configured successfully")
    print(f"   Form ID: {config.form_id}")
    print(f"   Form Title: {config.title}")
    print(f"   Field Name: {field.name}")
    print(f"   Field Type: {field.input_type}")
    print(f"   Field Required: {field.required}")
    
    # Test validation
    validator = FormValidator()
    test_data = {"test_field": ""}
    errors = validator.validate_required_fields(test_data, ["test_field"])
    
    if errors:
        print(f"✅ Validation working: {errors[0]}")
    
    print("✅ DRY form components test completed")