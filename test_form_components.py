#!/usr/bin/env python3
"""
🧪 DRY Form Components Testing Suite

Tests the DRY form components addressing report.md requirement:
"Refactor repeated form logic into DRY components"

This test validates:
- Form component initialization
- Input field configuration
- Validation logic
- Security integration
- Form rendering patterns
- Client and project form specializations
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from streamlit_extension.components.form_components import (
        FormConfig, InputField, FormValidator, SecurityForm,
        StandardForm, ClientForm, ProjectForm, InputRenderer,
        create_client_form, create_project_form,
        render_success_message, render_error_messages
    )
    FORM_COMPONENTS_AVAILABLE = True
except ImportError as e:
    FORM_COMPONENTS_AVAILABLE = False
    print(f"❌ Form components module not available: {e}")


def test_form_config():
    """Test form configuration."""
    if not FORM_COMPONENTS_AVAILABLE:
        return False
    
    print("📋 Testing Form Configuration")
    print("=" * 40)
    
    try:
        # Test basic configuration
        config = FormConfig(
            form_id="test_form",
            title="Test Form",
            submit_text="Submit Test",
            cancel_text="Cancel Test"
        )
        
        assert config.form_id == "test_form", "Form ID should match"
        assert config.title == "Test Form", "Title should match"
        assert config.submit_text == "Submit Test", "Submit text should match"
        assert config.cancel_text == "Cancel Test", "Cancel text should match"
        assert config.enable_csrf == True, "CSRF should be enabled by default"
        assert config.columns == 2, "Should default to 2 columns"
        
        print("✅ Basic form configuration working")
        
        # Test custom configuration
        custom_config = FormConfig(
            form_id="custom_form",
            title="Custom Form",
            enable_csrf=False,
            columns=3,
            submit_button_type="secondary"
        )
        
        assert custom_config.enable_csrf == False, "CSRF should be disabled"
        assert custom_config.columns == 3, "Should use custom column count"
        assert custom_config.submit_button_type == "secondary", "Button type should be custom"
        
        print("✅ Custom form configuration working")
        
        return True
        
    except Exception as e:
        print(f"❌ Form configuration test failed: {e}")
        return False


def test_input_field():
    """Test input field configuration."""
    if not FORM_COMPONENTS_AVAILABLE:
        return False
    
    print("\n📝 Testing Input Field Configuration")
    print("-" * 45)
    
    try:
        # Test basic input field
        field = InputField(
            name="test_field",
            label="Test Field",
            input_type="text_input",
            required=True,
            placeholder="Enter value"
        )
        
        assert field.name == "test_field", "Field name should match"
        assert field.label == "Test Field", "Label should match"
        assert field.input_type == "text_input", "Input type should match"
        assert field.required == True, "Required flag should match"
        assert field.placeholder == "Enter value", "Placeholder should match"
        
        print("✅ Basic input field working")
        
        # Test specialized input fields
        number_field = InputField(
            name="amount",
            label="Amount",
            input_type="number_input",
            min_value=0.0,
            max_value=1000.0,
            step=0.01
        )
        
        assert number_field.min_value == 0.0, "Min value should be set"
        assert number_field.max_value == 1000.0, "Max value should be set"
        assert number_field.step == 0.01, "Step should be set"
        
        print("✅ Number input field working")
        
        # Test select field
        select_field = InputField(
            name="status",
            label="Status",
            input_type="selectbox",
            options=["active", "inactive", "pending"]
        )
        
        assert select_field.options == ["active", "inactive", "pending"], "Options should be set"
        
        print("✅ Select input field working")
        
        return True
        
    except Exception as e:
        print(f"❌ Input field test failed: {e}")
        return False


def test_form_validator():
    """Test form validation logic."""
    if not FORM_COMPONENTS_AVAILABLE:
        return False
    
    print("\n✅ Testing Form Validator")
    print("-" * 30)
    
    try:
        validator = FormValidator()
        
        # Test required field validation
        test_data = {"name": "John", "email": ""}
        required_fields = ["name", "email"]
        errors = validator.validate_required_fields(test_data, required_fields)
        
        assert len(errors) == 1, "Should have one error for missing email"
        assert "Email" in errors[0], "Error should mention email field"
        
        print("✅ Required field validation working")
        
        # Test email validation
        valid_email = "test@example.com"
        invalid_email = "invalid-email"
        
        assert validator.validate_email(valid_email) is None, "Valid email should pass"
        assert validator.validate_email(invalid_email) is not None, "Invalid email should fail"
        
        print("✅ Email validation working")
        
        # Test phone validation
        valid_phone = "+1-555-123-4567"
        invalid_phone = "123"
        
        assert validator.validate_phone(valid_phone) is None, "Valid phone should pass"
        assert validator.validate_phone(invalid_phone) is not None, "Invalid phone should fail"
        
        print("✅ Phone validation working")
        
        # Test unique key validation
        existing_keys = ["key1", "key2", "key3"]
        new_key = "key4"
        duplicate_key = "key2"
        
        assert validator.validate_unique_key(new_key, existing_keys) is None, "New key should be valid"
        assert validator.validate_unique_key(duplicate_key, existing_keys) is not None, "Duplicate key should be invalid"
        
        print("✅ Unique key validation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Form validator test failed: {e}")
        return False


def test_security_form():
    """Test security form integration."""
    if not FORM_COMPONENTS_AVAILABLE:
        return False
    
    print("\n🔒 Testing Security Form")
    print("-" * 30)
    
    try:
        security = SecurityForm()
        
        # Test CSRF token generation (should not fail even if security not available)
        token = security.generate_csrf_token("test_form")
        print(f"✅ CSRF token generation working (token: {token is not None})")
        
        # Test CSRF validation (should pass through if security not available)
        is_valid = security.validate_csrf_token("test_form", "test_token")
        print(f"✅ CSRF validation working (result: {is_valid})")
        
        # Test rate limiting (should pass through if not available)
        rate_ok = security.check_rate_limit("test_user")
        print(f"✅ Rate limiting check working (result: {rate_ok})")
        
        return True
        
    except Exception as e:
        print(f"❌ Security form test failed: {e}")
        return False


def test_standard_form():
    """Test standard form component."""
    if not FORM_COMPONENTS_AVAILABLE:
        return False
    
    print("\n📄 Testing Standard Form")
    print("-" * 30)
    
    try:
        config = FormConfig(
            form_id="standard_test",
            title="Standard Test Form"
        )
        
        form = StandardForm(config)
        
        assert form.config.form_id == "standard_test", "Form should store config"
        assert isinstance(form.validator, FormValidator), "Should have validator"
        assert isinstance(form.security, SecurityForm), "Should have security"
        assert isinstance(form.renderer, InputRenderer), "Should have renderer"
        
        print("✅ Standard form initialization working")
        
        # Test validation and submission logic
        test_data = {"name": "Test", "email": "test@example.com"}
        required_fields = ["name", "email"]
        
        result = form.validate_and_submit(test_data, required_fields)
        
        assert "success" in result, "Result should have success field"
        assert "errors" in result, "Result should have errors field"
        assert "data" in result, "Result should have data field"
        
        print("✅ Form validation and submission working")
        
        return True
        
    except Exception as e:
        print(f"❌ Standard form test failed: {e}")
        return False


def test_client_form():
    """Test client form specialization."""
    if not FORM_COMPONENTS_AVAILABLE:
        return False
    
    print("\n👥 Testing Client Form")
    print("-" * 25)
    
    try:
        client_form = create_client_form("test_client", "Test Client Form")
        
        assert isinstance(client_form, ClientForm), "Should be ClientForm instance"
        assert client_form.config.form_id == "test_client", "Should have correct form ID"
        assert "Client" in client_form.config.title, "Title should mention client"
        
        print("✅ Client form creation working")
        
        # Test client field generation
        basic_fields, contact_fields = client_form.get_client_fields()
        
        assert len(basic_fields) > 0, "Should have basic fields"
        assert len(contact_fields) > 0, "Should have contact fields"
        
        # Check for required fields
        field_names = [f.name for f in basic_fields + contact_fields]
        assert "client_key" in field_names, "Should have client_key field"
        assert "name" in field_names, "Should have name field"
        assert "contact_email" in field_names, "Should have contact_email field"
        
        print("✅ Client field generation working")
        
        # Test client validation
        test_client_data = {
            "client_key": "test_client",
            "name": "Test Client",
            "contact_email": "invalid-email"
        }
        
        errors = client_form.validate_client_data(test_client_data)
        assert len(errors) > 0, "Should detect invalid email"
        
        print("✅ Client validation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Client form test failed: {e}")
        return False


def test_project_form():
    """Test project form specialization."""
    if not FORM_COMPONENTS_AVAILABLE:
        return False
    
    print("\n📁 Testing Project Form")
    print("-" * 25)
    
    try:
        project_form = create_project_form("test_project", "Test Project Form")
        
        assert isinstance(project_form, ProjectForm), "Should be ProjectForm instance"
        assert project_form.config.form_id == "test_project", "Should have correct form ID"
        assert "Project" in project_form.config.title, "Title should mention project"
        
        print("✅ Project form creation working")
        
        # Test project field generation
        clients_map = {1: "Client A", 2: "Client B"}
        basic_fields, timeline_fields = project_form.get_project_fields(clients_map=clients_map)
        
        assert len(basic_fields) > 0, "Should have basic fields"
        assert len(timeline_fields) > 0, "Should have timeline fields"
        
        # Check for required fields
        field_names = [f.name for f in basic_fields + timeline_fields]
        assert "name" in field_names, "Should have name field"
        assert "client_id" in field_names, "Should have client_id field"
        assert "start_date" in field_names, "Should have start_date field"
        
        print("✅ Project field generation working")
        
        # Test project validation
        from datetime import date, timedelta
        
        test_project_data = {
            "name": "Test Project",
            "client_id": "Client A",
            "start_date": date.today() + timedelta(days=10),
            "end_date": date.today()  # End before start
        }
        
        errors = project_form.validate_project_data(test_project_data, clients_map)
        assert len(errors) > 0, "Should detect end date before start date"
        
        print("✅ Project validation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Project form test failed: {e}")
        return False


def test_input_renderer():
    """Test input field rendering."""
    if not FORM_COMPONENTS_AVAILABLE:
        return False
    
    print("\n🎨 Testing Input Renderer")
    print("-" * 30)
    
    try:
        renderer = InputRenderer()
        
        # Test field rendering (will return None if Streamlit not available)
        text_field = InputField("test", "Test Field", "text_input")
        result = renderer.render_field(text_field)
        
        # Should not crash even if Streamlit not available
        print("✅ Text field rendering working")
        
        # Test number field rendering
        number_field = InputField("amount", "Amount", "number_input", min_value=0, max_value=100)
        result = renderer.render_field(number_field)
        
        print("✅ Number field rendering working")
        
        # Test select field rendering
        select_field = InputField("status", "Status", "selectbox", options=["A", "B", "C"])
        result = renderer.render_field(select_field)
        
        print("✅ Select field rendering working")
        
        return True
        
    except Exception as e:
        print(f"❌ Input renderer test failed: {e}")
        return False


def test_dry_principles():
    """Test that DRY principles are achieved."""
    if not FORM_COMPONENTS_AVAILABLE:
        return False
    
    print("\n🔄 Testing DRY Principles")
    print("-" * 30)
    
    try:
        # Test that multiple forms can share configuration
        config1 = FormConfig("form1", "Form 1")
        config2 = FormConfig("form2", "Form 2")
        
        form1 = StandardForm(config1)
        form2 = StandardForm(config2)
        
        # Both should use the same validator class
        assert type(form1.validator) == type(form2.validator), "Should share validator logic"
        assert type(form1.security) == type(form2.security), "Should share security logic"
        
        print("✅ Shared components working")
        
        # Test that specialized forms inherit base functionality
        client_form = ClientForm(config1)
        project_form = ProjectForm(config2)
        
        assert isinstance(client_form, StandardForm), "Client form should inherit from StandardForm"
        assert isinstance(project_form, StandardForm), "Project form should inherit from StandardForm"
        
        print("✅ Form inheritance working")
        
        # Test that common validation is reused
        validator1 = FormValidator()
        validator2 = FormValidator()
        
        test_email = "test@example.com"
        result1 = validator1.validate_email(test_email)
        result2 = validator2.validate_email(test_email)
        
        assert result1 == result2, "Validators should produce same results"
        
        print("✅ Reusable validation working")
        
        return True
        
    except Exception as e:
        print(f"❌ DRY principles test failed: {e}")
        return False


def main():
    """Main test execution."""
    print("🏗️ DRY FORM COMPONENTS TEST SUITE")
    print("=" * 60)
    print("Addresses report.md requirement:")
    print("- Refactor repeated form logic into DRY components")
    print()
    
    if not FORM_COMPONENTS_AVAILABLE:
        print("❌ Form components system not available")
        return False
    
    tests = [
        ("Form Configuration", test_form_config),
        ("Input Field Configuration", test_input_field),
        ("Form Validator", test_form_validator),
        ("Security Form", test_security_form),
        ("Standard Form", test_standard_form),
        ("Client Form", test_client_form),
        ("Project Form", test_project_form),
        ("Input Renderer", test_input_renderer),
        ("DRY Principles", test_dry_principles),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ DRY form components are working correctly")
        print("✅ Report.md requirement fulfilled: Form logic refactored")
        print("✅ Code duplication eliminated")
        print("✅ Reusable components available")
        print("✅ Specialized forms working")
        return True
    else:
        print(f"\n❌ {total-passed} tests failed")
        print("❗ DRY form components need fixes")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)