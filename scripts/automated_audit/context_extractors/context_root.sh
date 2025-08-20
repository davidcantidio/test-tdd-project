#!/bin/bash

# 🏠 CONTEXT EXTRACTION SCRIPT - ROOT DIRECTORY
# Purpose: Extract comprehensive context from root documentation for systematic file auditor
# Created: 2025-08-19 (Sétima Camada - Context Extraction System)
# Usage: ./context_root.sh [output_file]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
# Ensure we're in the test-tdd-project directory
if [[ "$(basename "$PROJECT_ROOT")" != "test-tdd-project" ]]; then
    PROJECT_ROOT="$PROJECT_ROOT/test-tdd-project"
fi
DEFAULT_OUTPUT_FILE="$PROJECT_ROOT/scripts/automated_audit/context_cache/root_context.json"
OUTPUT_FILE="${1:-$DEFAULT_OUTPUT_FILE}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo -e "${BLUE}🏠 ROOT CONTEXT EXTRACTION${NC}"
echo "=========================================="
echo "Project Root: $PROJECT_ROOT"
echo "Output File: $OUTPUT_FILE"
echo "Timestamp: $TIMESTAMP"
echo ""

# Create output directory
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Initialize context object
cat > "$OUTPUT_FILE" << 'EOF'
{
  "context_type": "root_directory",
  "extraction_timestamp": "",
  "project_overview": {},
  "architecture_summary": {},
  "tdd_integration": {},
  "tdah_optimization": {},
  "documentation_structure": {},
  "system_status": {},
  "development_guidelines": {},
  "extracted_files": []
}
EOF

# Function to extract file content safely
extract_file_content() {
    local file_path="$1"
    local content_key="$2"
    
    if [[ -f "$file_path" ]]; then
        echo -e "${GREEN}✅ Extracting: $file_path${NC}"
        
        # Extract key sections using jq to safely add to JSON
        local content
        content=$(cat "$file_path" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
        
        # Add to extracted files list
        jq --arg file "$file_path" --arg content "$content" --arg key "$content_key" \
           '.extracted_files += [{"file": $file, "content_key": $key, "size": ($content | length), "status": "extracted"}]' \
           "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
        
        return 0
    else
        echo -e "${YELLOW}⚠️ File not found: $file_path${NC}"
        
        # Add to extracted files list as missing
        jq --arg file "$file_path" --arg key "$content_key" \
           '.extracted_files += [{"file": $file, "content_key": $key, "size": 0, "status": "missing"}]' \
           "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
        
        return 1
    fi
}

# Function to extract section from markdown file
extract_markdown_section() {
    local file_path="$1"
    local section_name="$2"
    local json_key="$3"
    
    if [[ -f "$file_path" ]]; then
        echo -e "${BLUE}📋 Extracting section '$section_name' from $file_path${NC}"
        
        # Extract section content
        local section_content
        section_content=$(awk "/^#+ .*$section_name/,/^#+ / {if (/^#+ / && !/^#+ .*$section_name/) exit; print}" "$file_path" | head -n -1)
        
        if [[ -n "$section_content" ]]; then
            # Safely add to JSON
            section_content=$(echo "$section_content" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
            jq --arg content "$section_content" --arg key "$json_key" \
               '.[$key] = $content' \
               "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
            
            echo -e "${GREEN}  ✅ Section extracted successfully${NC}"
            return 0
        else
            echo -e "${YELLOW}  ⚠️ Section '$section_name' not found${NC}"
            return 1
        fi
    else
        echo -e "${RED}  ❌ File not found: $file_path${NC}"
        return 1
    fi
}

# Start extraction process
echo -e "${BLUE}📊 Starting context extraction...${NC}"

# Update timestamp
jq --arg timestamp "$TIMESTAMP" '.extraction_timestamp = $timestamp' "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

# 1. Extract CLAUDE.md (Main project documentation)
echo -e "\n${BLUE}📄 Processing CLAUDE.md (Main Documentation)${NC}"
CLAUDE_MD="$PROJECT_ROOT/CLAUDE.md"

if extract_file_content "$CLAUDE_MD" "main_documentation"; then
    # Extract key sections from CLAUDE.md
    extract_markdown_section "$CLAUDE_MD" "Project Overview" "project_overview"
    extract_markdown_section "$CLAUDE_MD" "TDD.*TDAH.*INTEGRATION" "tdd_tdah_integration"  
    extract_markdown_section "$CLAUDE_MD" "Module Architecture" "module_architecture"
    extract_markdown_section "$CLAUDE_MD" "Current Status" "current_status"
    extract_markdown_section "$CLAUDE_MD" "Security.*Status" "security_status"
    extract_markdown_section "$CLAUDE_MD" "Quick Start" "quick_start"
    extract_markdown_section "$CLAUDE_MD" "System Metrics" "system_metrics"
fi

# 2. Extract INDEX.md (Navigation structure)
echo -e "\n${BLUE}🗂️ Processing INDEX.md (Navigation Structure)${NC}"
INDEX_MD="$PROJECT_ROOT/INDEX.md"

if extract_file_content "$INDEX_MD" "navigation_structure"; then
    extract_markdown_section "$INDEX_MD" "Project Structure" "project_structure"
    extract_markdown_section "$INDEX_MD" "Quick Navigation" "quick_navigation"
    extract_markdown_section "$INDEX_MD" "Module Overview" "module_overview"
fi

# 3. Extract NAVIGATION.md (Advanced navigation)
echo -e "\n${BLUE}🧭 Processing NAVIGATION.md (Advanced Navigation)${NC}"
NAVIGATION_MD="$PROJECT_ROOT/NAVIGATION.md"

if extract_file_content "$NAVIGATION_MD" "advanced_navigation"; then
    extract_markdown_section "$NAVIGATION_MD" "Development Workflow" "development_workflow"
    extract_markdown_section "$NAVIGATION_MD" "Testing.*Strategy" "testing_strategy"
    extract_markdown_section "$NAVIGATION_MD" "Architecture.*Guide" "architecture_guide"
fi

# 4. Extract README.md (Project introduction)
echo -e "\n${BLUE}📖 Processing README.md (Project Introduction)${NC}"
README_MD="$PROJECT_ROOT/README.md"

if extract_file_content "$README_MD" "project_introduction"; then
    extract_markdown_section "$README_MD" "Getting Started" "getting_started"
    extract_markdown_section "$README_MD" "Features" "features_overview"
    extract_markdown_section "$README_MD" "Installation" "installation_guide"
fi

# 5. Extract TROUBLESHOOTING.md (Common issues and solutions)
echo -e "\n${BLUE}🔧 Processing TROUBLESHOOTING.md (Problem Resolution)${NC}"
TROUBLESHOOTING_MD="$PROJECT_ROOT/TROUBLESHOOTING.md"

if extract_file_content "$TROUBLESHOOTING_MD" "troubleshooting_guide"; then
    extract_markdown_section "$TROUBLESHOOTING_MD" "Common Issues" "common_issues"
    extract_markdown_section "$TROUBLESHOOTING_MD" "Performance.*Issues" "performance_troubleshooting"
    extract_markdown_section "$TROUBLESHOOTING_MD" "Database.*Issues" "database_troubleshooting"
fi

# 6. Extract .gitignore patterns (Project exclusions)
echo -e "\n${BLUE}🚫 Processing .gitignore (Project Exclusions)${NC}"
GITIGNORE_FILE="$PROJECT_ROOT/.gitignore"

if [[ -f "$GITIGNORE_FILE" ]]; then
    echo -e "${GREEN}✅ Extracting: $GITIGNORE_FILE${NC}"
    
    # Extract gitignore patterns
    local gitignore_content
    gitignore_content=$(grep -v '^#' "$GITIGNORE_FILE" | grep -v '^$' | head -20 | tr '\n' ',' | sed 's/,$//')
    
    jq --arg patterns "$gitignore_content" '.project_exclusions = $patterns' \
       "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
    
    jq --arg file "$GITIGNORE_FILE" \
       '.extracted_files += [{"file": $file, "content_key": "project_exclusions", "size": ($patterns | length), "status": "patterns_extracted"}]' \
       "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
else
    echo -e "${YELLOW}⚠️ .gitignore not found${NC}"
fi

# 7. Extract Python package info
echo -e "\n${BLUE}🐍 Processing Python Package Information${NC}"

# Check for requirements.txt
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
if [[ -f "$REQUIREMENTS_FILE" ]]; then
    echo -e "${GREEN}✅ Extracting: $REQUIREMENTS_FILE${NC}"
    
    local requirements_content
    requirements_content=$(head -10 "$REQUIREMENTS_FILE" | tr '\n' ',' | sed 's/,$//')
    
    jq --arg reqs "$requirements_content" '.python_dependencies = $reqs' \
       "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
fi

# Check for setup.py or pyproject.toml
for file in "setup.py" "pyproject.toml"; do
    if [[ -f "$PROJECT_ROOT/$file" ]]; then
        echo -e "${GREEN}✅ Found: $file${NC}"
        jq --arg file "$file" '.package_config = $file' \
           "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
        break
    fi
done

# 8. Extract development guidelines from any DEVELOPMENT.md or CONTRIBUTING.md
echo -e "\n${BLUE}👥 Processing Development Guidelines${NC}"

for guidelines_file in "DEVELOPMENT.md" "CONTRIBUTING.md" "DEVELOPMENT_GUIDE.md"; do
    GUIDELINES_PATH="$PROJECT_ROOT/$guidelines_file"
    if [[ -f "$GUIDELINES_PATH" ]]; then
        echo -e "${GREEN}✅ Extracting: $GUIDELINES_PATH${NC}"
        
        extract_markdown_section "$GUIDELINES_PATH" "Guidelines" "development_guidelines"
        extract_markdown_section "$GUIDELINES_PATH" "Standards" "coding_standards"
        extract_markdown_section "$GUIDELINES_PATH" "Workflow" "development_workflow"
        break
    fi
done

# 9. Project structure analysis
echo -e "\n${BLUE}🏗️ Analyzing Project Structure${NC}"

# Count directories and files
DIR_COUNT=$(find "$PROJECT_ROOT" -maxdepth 2 -type d | wc -l)
FILE_COUNT=$(find "$PROJECT_ROOT" -maxdepth 2 -type f -name "*.py" | wc -l)
MD_COUNT=$(find "$PROJECT_ROOT" -maxdepth 2 -type f -name "*.md" | wc -l)

# Get main directories
MAIN_DIRS=$(ls -la "$PROJECT_ROOT" | grep '^d' | awk '{print $9}' | grep -v '^\.\.$' | grep -v '^\.$' | head -10 | tr '\n' ',' | sed 's/,$//')

jq --arg dirs "$DIR_COUNT" --arg files "$FILE_COUNT" --arg mds "$MD_COUNT" --arg main_dirs "$MAIN_DIRS" \
   '.project_statistics = {"directories": $dirs, "python_files": $files, "markdown_files": $mds, "main_directories": $main_dirs}' \
   "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

# 10. TDD and TDAH context extraction
echo -e "\n${BLUE}🎯 Extracting TDD and TDAH Context${NC}"

# Search for TDD-related content across documentation
TDD_MATCHES=$(grep -r -i "tdd\|test.*driven\|red.*green.*refactor" "$PROJECT_ROOT"/*.md 2>/dev/null | wc -l || echo "0")
TDAH_MATCHES=$(grep -r -i "tdah\|adhd\|focus.*session\|hyperfocus" "$PROJECT_ROOT"/*.md 2>/dev/null | wc -l || echo "0")

jq --arg tdd_matches "$TDD_MATCHES" --arg tdah_matches "$TDAH_MATCHES" \
   '.context_analysis = {"tdd_references": $tdd_matches, "tdah_references": $tdah_matches}' \
   "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

# 11. Final context summary
echo -e "\n${BLUE}📋 Generating Context Summary${NC}"

# Count extracted files
EXTRACTED_COUNT=$(jq '.extracted_files | length' "$OUTPUT_FILE")
SUCCESS_COUNT=$(jq '.extracted_files | map(select(.status != "missing")) | length' "$OUTPUT_FILE")

# Add extraction summary
jq --arg extracted "$EXTRACTED_COUNT" --arg success "$SUCCESS_COUNT" --arg timestamp "$TIMESTAMP" \
   '.extraction_summary = {"total_files_processed": $extracted, "successful_extractions": $success, "completion_timestamp": $timestamp}' \
   "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

# Validation and final output
echo -e "\n${GREEN}✅ Context extraction completed!${NC}"
echo "=========================================="
echo -e "${BLUE}📊 Extraction Summary:${NC}"
echo "  • Files processed: $EXTRACTED_COUNT"
echo "  • Successful extractions: $SUCCESS_COUNT"
echo "  • Output file: $OUTPUT_FILE"
echo "  • Output size: $(du -h "$OUTPUT_FILE" | cut -f1)"

# Validate JSON format
if jq empty "$OUTPUT_FILE" 2>/dev/null; then
    echo -e "${GREEN}  ✅ JSON format valid${NC}"
else
    echo -e "${RED}  ❌ JSON format invalid${NC}"
    exit 1
fi

# Display extraction results
echo -e "\n${BLUE}🎯 Context Analysis Results:${NC}"
TDD_REFS=$(jq -r '.context_analysis.tdd_references' "$OUTPUT_FILE")
TDAH_REFS=$(jq -r '.context_analysis.tdah_references' "$OUTPUT_FILE")
echo "  • TDD references found: $TDD_REFS"
echo "  • TDAH references found: $TDAH_REFS"

MAIN_DIRECTORIES=$(jq -r '.project_statistics.main_directories' "$OUTPUT_FILE")
echo "  • Main directories: $MAIN_DIRECTORIES"

echo -e "\n${GREEN}🏆 Root context extraction completed successfully!${NC}"
echo "Ready for systematic file auditor integration."
echo ""

# Optional: Display context file for verification
if [[ "${2:-}" == "--show" ]]; then
    echo -e "${BLUE}📄 Generated Context (first 50 lines):${NC}"
    echo "----------------------------------------"
    head -50 "$OUTPUT_FILE"
    echo "----------------------------------------"
fi

exit 0