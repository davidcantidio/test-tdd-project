#!/bin/bash

# 📱 CONTEXT EXTRACTION SCRIPT - STREAMLIT EXTENSION MODULE
# Purpose: Extract comprehensive context from streamlit_extension module for systematic file auditor
# Created: 2025-08-19 (Sétima Camada - Context Extraction System)
# Usage: ./context_streamlit.sh [output_file]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
# Ensure we're in the test-tdd-project directory
if [[ "$(basename "$PROJECT_ROOT")" != "test-tdd-project" ]]; then
    PROJECT_ROOT="$PROJECT_ROOT/test-tdd-project"
fi
STREAMLIT_MODULE="$PROJECT_ROOT/streamlit_extension"
DEFAULT_OUTPUT_FILE="$PROJECT_ROOT/scripts/automated_audit/context_cache/streamlit_context.json"
OUTPUT_FILE="${1:-$DEFAULT_OUTPUT_FILE}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo -e "${CYAN}📱 STREAMLIT EXTENSION CONTEXT EXTRACTION${NC}"
echo "=============================================="
echo "Project Root: $PROJECT_ROOT"
echo "Streamlit Module: $STREAMLIT_MODULE"
echo "Output File: $OUTPUT_FILE"
echo "Timestamp: $TIMESTAMP"
echo ""

# Verify streamlit_extension exists
if [[ ! -d "$STREAMLIT_MODULE" ]]; then
    echo -e "${RED}❌ Error: streamlit_extension directory not found at $STREAMLIT_MODULE${NC}"
    exit 1
fi

# Create output directory
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Initialize context object
cat > "$OUTPUT_FILE" << 'EOF'
{
  "context_type": "streamlit_extension_module",
  "extraction_timestamp": "",
  "module_overview": {},
  "architecture_patterns": {},
  "authentication_system": {},
  "component_architecture": {},
  "database_layer": {},
  "api_endpoints": {},
  "service_layer": {},
  "utilities_framework": {},
  "middleware_stack": {},
  "configuration_system": {},
  "extracted_files": [],
  "module_statistics": {},
  "dependency_analysis": {}
}
EOF

# Function to extract file content safely
extract_file_content() {
    local file_path="$1"
    local content_key="$2"
    local description="${3:-}"
    
    if [[ -f "$file_path" ]]; then
        echo -e "${GREEN}✅ Extracting: $file_path${NC}"
        [[ -n "$description" ]] && echo -e "   ${BLUE}📋 $description${NC}"
        
        # Get file size
        local file_size=$(wc -c < "$file_path")
        
        # Add to extracted files list with metadata
        jq --arg file "$file_path" --arg key "$content_key" --arg size "$file_size" --arg desc "$description" \
           '.extracted_files += [{"file": $file, "content_key": $key, "size": ($size | tonumber), "description": $desc, "status": "extracted"}]' \
           "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
        
        return 0
    else
        echo -e "${YELLOW}⚠️ File not found: $file_path${NC}"
        
        # Add to extracted files list as missing
        jq --arg file "$file_path" --arg key "$content_key" --arg desc "$description" \
           '.extracted_files += [{"file": $file, "content_key": $key, "size": 0, "description": $desc, "status": "missing"}]' \
           "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
        
        return 1
    fi
}

# Function to extract section from markdown file
extract_markdown_section() {
    local file_path="$1"
    local section_pattern="$2"
    local json_key="$3"
    
    if [[ -f "$file_path" ]]; then
        echo -e "${BLUE}📋 Extracting section pattern '$section_pattern' from $(basename "$file_path")${NC}"
        
        # Extract section content using simple grep approach
        local section_content
        section_content=$(awk "/^#+ .*$section_pattern/,/^#+ / {if (/^#+ / && !/^#+ .*$section_pattern/) exit; print}" "$file_path" | head -n -1)
        
        if [[ -n "$section_content" ]]; then
            # Safely add to JSON
            section_content=$(echo "$section_content" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
            jq --arg content "$section_content" --arg key "$json_key" \
               '.[$key] = $content' \
               "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
            
            echo -e "${GREEN}  ✅ Section extracted successfully ($(echo "$section_content" | wc -c) chars)${NC}"
            return 0
        else
            echo -e "${YELLOW}  ⚠️ Section pattern '$section_pattern' not found${NC}"
            return 1
        fi
    else
        echo -e "${RED}  ❌ File not found: $file_path${NC}"
        return 1
    fi
}

# Function to analyze Python module structure
analyze_python_module() {
    local module_path="$1"
    local module_name="$2"
    
    echo -e "${BLUE}🐍 Analyzing Python module: $module_name${NC}"
    
    if [[ -d "$module_path" ]]; then
        # Count files
        local py_files=$(find "$module_path" -name "*.py" | wc -l)
        local init_files=$(find "$module_path" -name "__init__.py" | wc -l)
        local subdirs=$(find "$module_path" -maxdepth 1 -type d | grep -v "^$module_path$" | wc -l)
        
        # Get main Python files (top level)
        local main_files
        main_files=$(find "$module_path" -maxdepth 1 -name "*.py" ! -name "__init__.py" | xargs -I {} basename {} | head -5 | tr '\n' ',' | sed 's/,$//')
        
        # Add to JSON
        jq --arg module "$module_name" --arg py_count "$py_files" --arg init_count "$init_files" \
           --arg subdir_count "$subdirs" --arg main_files "$main_files" \
           '.module_statistics.'"$module_name"' = {"python_files": ($py_count | tonumber), "init_files": ($init_count | tonumber), "subdirectories": ($subdir_count | tonumber), "main_files": $main_files}' \
           "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
        
        echo -e "${GREEN}  ✅ Module analysis: $py_files Python files, $subdirs subdirectories${NC}"
        return 0
    else
        echo -e "${YELLOW}  ⚠️ Module directory not found: $module_path${NC}"
        return 1
    fi
}

# Start extraction process
echo -e "${BLUE}📊 Starting streamlit_extension context extraction...${NC}"

# Update timestamp
jq --arg timestamp "$TIMESTAMP" '.extraction_timestamp = $timestamp' "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

# 1. Extract main streamlit_extension/CLAUDE.md
echo -e "\n${CYAN}📄 Processing Main Module Documentation${NC}"
MAIN_CLAUDE_MD="$STREAMLIT_MODULE/CLAUDE.md"

if extract_file_content "$MAIN_CLAUDE_MD" "main_module_documentation" "Primary streamlit extension documentation"; then
    # Extract key sections from main CLAUDE.md
    extract_markdown_section "$MAIN_CLAUDE_MD" "Module Overview" "module_overview"
    extract_markdown_section "$MAIN_CLAUDE_MD" "Architecture.*Patterns" "architecture_patterns"
    extract_markdown_section "$MAIN_CLAUDE_MD" "Component.*System" "component_system"
    extract_markdown_section "$MAIN_CLAUDE_MD" "Service.*Layer" "service_layer_overview"
    extract_markdown_section "$MAIN_CLAUDE_MD" "Database.*Integration" "database_integration"
    extract_markdown_section "$MAIN_CLAUDE_MD" "Performance.*Optimization" "performance_optimization"
fi

# 2. Extract Authentication System Documentation
echo -e "\n${CYAN}🔐 Processing Authentication System${NC}"
AUTH_CLAUDE_MD="$STREAMLIT_MODULE/auth/CLAUDE.md"

if extract_file_content "$AUTH_CLAUDE_MD" "authentication_documentation" "Authentication system architecture and security"; then
    extract_markdown_section "$AUTH_CLAUDE_MD" "Authentication.*Architecture" "auth_architecture"
    extract_markdown_section "$AUTH_CLAUDE_MD" "Security.*Implementation" "security_implementation"
    extract_markdown_section "$AUTH_CLAUDE_MD" "Session.*Management" "session_management"
    extract_markdown_section "$AUTH_CLAUDE_MD" "OAuth.*Integration" "oauth_integration"
fi

# Also extract key auth Python files
extract_file_content "$STREAMLIT_MODULE/auth/auth_manager.py" "auth_manager_implementation" "Core authentication manager"
extract_file_content "$STREAMLIT_MODULE/auth/session_handler.py" "session_handler_implementation" "Session handling logic"

# 3. Extract Components System Documentation
echo -e "\n${CYAN}🧩 Processing Components System${NC}"
COMPONENTS_CLAUDE_MD="$STREAMLIT_MODULE/components/CLAUDE.md"

if extract_file_content "$COMPONENTS_CLAUDE_MD" "components_documentation" "UI components architecture and patterns"; then
    extract_markdown_section "$COMPONENTS_CLAUDE_MD" "Component.*Architecture" "component_architecture"
    extract_markdown_section "$COMPONENTS_CLAUDE_MD" "Widget.*System" "widget_system"
    extract_markdown_section "$COMPONENTS_CLAUDE_MD" "Layout.*Management" "layout_management"
    extract_markdown_section "$COMPONENTS_CLAUDE_MD" "Form.*Components" "form_components"
fi

# Extract key component files
extract_file_content "$STREAMLIT_MODULE/components/dashboard_widgets.py" "dashboard_widgets_implementation" "Main dashboard widgets"
extract_file_content "$STREAMLIT_MODULE/components/form_components.py" "form_components_implementation" "Reusable form components"

# 4. Extract Database Layer Documentation
echo -e "\n${CYAN}🗄️ Processing Database Layer${NC}"
DATABASE_CLAUDE_MD="$STREAMLIT_MODULE/database/CLAUDE.md"

if extract_file_content "$DATABASE_CLAUDE_MD" "database_documentation" "Database layer architecture and queries"; then
    extract_markdown_section "$DATABASE_CLAUDE_MD" "Database.*Architecture" "database_architecture"
    extract_markdown_section "$DATABASE_CLAUDE_MD" "Connection.*Management" "connection_management"
    extract_markdown_section "$DATABASE_CLAUDE_MD" "Query.*Optimization" "query_optimization"
    extract_markdown_section "$DATABASE_CLAUDE_MD" "Migration.*System" "migration_system"
fi

# Extract key database files
extract_file_content "$STREAMLIT_MODULE/database/connection.py" "database_connection_implementation" "Database connection manager"
extract_file_content "$STREAMLIT_MODULE/database/queries.py" "database_queries_implementation" "Core database queries"
extract_file_content "$STREAMLIT_MODULE/database/schema.py" "database_schema_implementation" "Database schema definition"

# 5. Extract API Endpoints Documentation
echo -e "\n${CYAN}🌐 Processing API Endpoints${NC}"
ENDPOINTS_CLAUDE_MD="$STREAMLIT_MODULE/endpoints/CLAUDE.md"

if extract_file_content "$ENDPOINTS_CLAUDE_MD" "endpoints_documentation" "API endpoints and middleware"; then
    extract_markdown_section "$ENDPOINTS_CLAUDE_MD" "API.*Architecture" "api_architecture"
    extract_markdown_section "$ENDPOINTS_CLAUDE_MD" "Endpoint.*Design" "endpoint_design"
    extract_markdown_section "$ENDPOINTS_CLAUDE_MD" "Middleware.*Stack" "middleware_stack"
    extract_markdown_section "$ENDPOINTS_CLAUDE_MD" "Rate.*Limiting" "rate_limiting"
fi

# Extract API README if exists
extract_file_content "$STREAMLIT_MODULE/endpoints/README_API.md" "api_readme" "API usage and examples"

# 6. Extract Service Layer Documentation
echo -e "\n${CYAN}⚙️ Processing Service Layer${NC}"
SERVICES_CLAUDE_MD="$STREAMLIT_MODULE/services/CLAUDE.md"

if extract_file_content "$SERVICES_CLAUDE_MD" "services_documentation" "Business logic and service layer"; then
    extract_markdown_section "$SERVICES_CLAUDE_MD" "Service.*Architecture" "service_architecture"
    extract_markdown_section "$SERVICES_CLAUDE_MD" "Business.*Logic" "business_logic"
    extract_markdown_section "$SERVICES_CLAUDE_MD" "Dependency.*Injection" "dependency_injection"
    extract_markdown_section "$SERVICES_CLAUDE_MD" "Transaction.*Management" "transaction_management"
fi

# Extract key service files
extract_file_content "$STREAMLIT_MODULE/services/base.py" "base_service_implementation" "Base service abstract class"
extract_file_content "$STREAMLIT_MODULE/services/service_container.py" "service_container_implementation" "Dependency injection container"

# 7. Extract Models Documentation
echo -e "\n${CYAN}📊 Processing Data Models${NC}"
MODELS_CLAUDE_MD="$STREAMLIT_MODULE/models/CLAUDE.md"

if extract_file_content "$MODELS_CLAUDE_MD" "models_documentation" "Data models and domain objects"; then
    extract_markdown_section "$MODELS_CLAUDE_MD" "Model.*Architecture" "model_architecture"
    extract_markdown_section "$MODELS_CLAUDE_MD" "Domain.*Objects" "domain_objects"
    extract_markdown_section "$MODELS_CLAUDE_MD" "Validation.*Rules" "validation_rules"
    extract_markdown_section "$MODELS_CLAUDE_MD" "TDD.*Integration" "tdd_integration"
fi

# 8. Extract Utilities Documentation
echo -e "\n${CYAN}🔧 Processing Utilities Framework${NC}"
UTILS_CLAUDE_MD="$STREAMLIT_MODULE/utils/CLAUDE.md"

if extract_file_content "$UTILS_CLAUDE_MD" "utils_documentation" "Utility functions and helpers"; then
    extract_markdown_section "$UTILS_CLAUDE_MD" "Utility.*Architecture" "utility_architecture"
    extract_markdown_section "$UTILS_CLAUDE_MD" "Cache.*System" "cache_system"
    extract_markdown_section "$UTILS_CLAUDE_MD" "Security.*Utilities" "security_utilities"
    extract_markdown_section "$UTILS_CLAUDE_MD" "Performance.*Tools" "performance_tools"
fi

# Extract key utility files
extract_file_content "$STREAMLIT_MODULE/utils/database.py" "database_utils_implementation" "Database utility functions"
extract_file_content "$STREAMLIT_MODULE/utils/app_setup.py" "app_setup_implementation" "Application setup and initialization"

# 9. Extract Middleware Documentation
echo -e "\n${CYAN}🛡️ Processing Middleware Stack${NC}"
MIDDLEWARE_CLAUDE_MD="$STREAMLIT_MODULE/middleware/rate_limiting/CLAUDE.md"

if extract_file_content "$MIDDLEWARE_CLAUDE_MD" "middleware_documentation" "Rate limiting and middleware"; then
    extract_markdown_section "$MIDDLEWARE_CLAUDE_MD" "Rate.*Limiting.*Architecture" "rate_limiting_architecture"
    extract_markdown_section "$MIDDLEWARE_CLAUDE_MD" "Algorithm.*Implementation" "algorithm_implementation"
    extract_markdown_section "$MIDDLEWARE_CLAUDE_MD" "Policy.*Management" "policy_management"
fi

# 10. Extract Main Application Files
echo -e "\n${CYAN}🏠 Processing Main Application${NC}"
extract_file_content "$STREAMLIT_MODULE/streamlit_app.py" "main_application" "Primary Streamlit application entry point"
extract_file_content "$STREAMLIT_MODULE/__init__.py" "module_init" "Module initialization and exports"

# 11. Analyze Module Structure
echo -e "\n${CYAN}🏗️ Analyzing Module Structure${NC}"

# Analyze each major submodule
for submodule in "auth" "components" "database" "endpoints" "services" "utils" "models" "config" "middleware"; do
    if [[ -d "$STREAMLIT_MODULE/$submodule" ]]; then
        analyze_python_module "$STREAMLIT_MODULE/$submodule" "$submodule"
    fi
done

# 12. Extract Configuration System
echo -e "\n${CYAN}⚙️ Processing Configuration System${NC}"
extract_file_content "$STREAMLIT_MODULE/config/constants.py" "configuration_constants" "System constants and enums"
extract_file_content "$STREAMLIT_MODULE/config/environment.py" "environment_config" "Environment configuration management"
extract_file_content "$STREAMLIT_MODULE/config/feature_flags.py" "feature_flags" "Feature flag system"

# 13. Dependency Analysis
echo -e "\n${CYAN}🔗 Analyzing Dependencies${NC}"

# Count imports and dependencies
IMPORT_COUNT=$(find "$STREAMLIT_MODULE" -name "*.py" -exec grep -h "^import\|^from.*import" {} \; 2>/dev/null | sort | uniq | wc -l)
INTERNAL_IMPORTS=$(find "$STREAMLIT_MODULE" -name "*.py" -exec grep -h "from streamlit_extension" {} \; 2>/dev/null | wc -l)
EXTERNAL_IMPORTS=$(find "$STREAMLIT_MODULE" -name "*.py" -exec grep -h "import streamlit\|import pandas\|import numpy" {} \; 2>/dev/null | wc -l)

# Get top external dependencies
TOP_DEPS=$(find "$STREAMLIT_MODULE" -name "*.py" -exec grep -ho "^import [a-zA-Z_][a-zA-Z0-9_]*" {} \; 2>/dev/null | cut -d' ' -f2 | sort | uniq -c | sort -nr | head -5 | awk '{print $2}' | tr '\n' ',' | sed 's/,$//')

jq --arg total_imports "$IMPORT_COUNT" --arg internal_imports "$INTERNAL_IMPORTS" \
   --arg external_imports "$EXTERNAL_IMPORTS" --arg top_deps "$TOP_DEPS" \
   '.dependency_analysis = {"total_imports": ($total_imports | tonumber), "internal_imports": ($internal_imports | tonumber), "external_imports": ($external_imports | tonumber), "top_dependencies": $top_deps}' \
   "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

# 14. Final Statistics
echo -e "\n${CYAN}📊 Generating Final Statistics${NC}"

# Count extracted files
EXTRACTED_COUNT=$(jq '.extracted_files | length' "$OUTPUT_FILE")
SUCCESS_COUNT=$(jq '.extracted_files | map(select(.status != "missing")) | length' "$OUTPUT_FILE")
TOTAL_SIZE=$(jq '.extracted_files | map(select(.status == "extracted")) | map(.size) | add // 0' "$OUTPUT_FILE")

# Add extraction summary
jq --arg extracted "$EXTRACTED_COUNT" --arg success "$SUCCESS_COUNT" \
   --arg total_size "$TOTAL_SIZE" --arg timestamp "$TIMESTAMP" \
   '.extraction_summary = {"total_files_processed": ($extracted | tonumber), "successful_extractions": ($success | tonumber), "total_extracted_size": ($total_size | tonumber), "completion_timestamp": $timestamp}' \
   "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

# Validation and final output
echo -e "\n${GREEN}✅ Streamlit extension context extraction completed!${NC}"
echo "=============================================="
echo -e "${CYAN}📊 Extraction Summary:${NC}"
echo "  • Files processed: $EXTRACTED_COUNT"
echo "  • Successful extractions: $SUCCESS_COUNT"
echo "  • Total extracted size: $(numfmt --to=iec $TOTAL_SIZE 2>/dev/null || echo "$TOTAL_SIZE") bytes"
echo "  • Output file: $OUTPUT_FILE"
echo "  • Output size: $(du -h "$OUTPUT_FILE" | cut -f1)"

# Validate JSON format
if jq empty "$OUTPUT_FILE" 2>/dev/null; then
    echo -e "${GREEN}  ✅ JSON format valid${NC}"
else
    echo -e "${RED}  ❌ JSON format invalid${NC}"
    exit 1
fi

# Display dependency analysis
echo -e "\n${CYAN}🔗 Dependency Analysis Results:${NC}"
echo "  • Total imports: $IMPORT_COUNT"
echo "  • Internal imports: $INTERNAL_IMPORTS"
echo "  • Top dependencies: $TOP_DEPS"

# Display module statistics
echo -e "\n${CYAN}🏗️ Module Statistics:${NC}"
TOTAL_PY_FILES=$(find "$STREAMLIT_MODULE" -name "*.py" | wc -l)
TOTAL_SUBDIRS=$(find "$STREAMLIT_MODULE" -type d | wc -l)
echo "  • Total Python files: $TOTAL_PY_FILES"
echo "  • Total subdirectories: $TOTAL_SUBDIRS"

echo -e "\n${GREEN}🏆 Streamlit extension context extraction completed successfully!${NC}"
echo "Ready for systematic file auditor integration."
echo ""

# Optional: Display context file for verification
if [[ "${2:-}" == "--show" ]]; then
    echo -e "${CYAN}📄 Generated Context (first 50 lines):${NC}"
    echo "----------------------------------------"
    head -50 "$OUTPUT_FILE"
    echo "----------------------------------------"
fi

exit 0