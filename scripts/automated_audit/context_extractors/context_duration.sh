#!/bin/bash

# ⏱️ CONTEXT EXTRACTION SCRIPT - DURATION SYSTEM MODULE
# Purpose: Extract comprehensive context from duration_system module for systematic file auditor
# Created: 2025-08-19 (Sétima Camada - Context Extraction System)
# Usage: ./context_duration.sh [output_file]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
# Ensure we're in the test-tdd-project directory
if [[ "$(basename "$PROJECT_ROOT")" != "test-tdd-project" ]]; then
    PROJECT_ROOT="$PROJECT_ROOT/test-tdd-project"
fi
DURATION_MODULE="$PROJECT_ROOT/duration_system"
DEFAULT_OUTPUT_FILE="$PROJECT_ROOT/scripts/automated_audit/context_cache/duration_context.json"
OUTPUT_FILE="${1:-$DEFAULT_OUTPUT_FILE}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo -e "${PURPLE}⏱️ DURATION SYSTEM CONTEXT EXTRACTION${NC}"
echo "=============================================="
echo "Project Root: $PROJECT_ROOT"
echo "Duration Module: $DURATION_MODULE"
echo "Output File: $OUTPUT_FILE"
echo "Timestamp: $TIMESTAMP"
echo ""

# Verify duration_system exists
if [[ ! -d "$DURATION_MODULE" ]]; then
    echo -e "${RED}❌ Error: duration_system directory not found at $DURATION_MODULE${NC}"
    exit 1
fi

# Create output directory
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Initialize context object
cat > "$OUTPUT_FILE" << 'EOF'
{
  "context_type": "duration_system_module",
  "extraction_timestamp": "",
  "module_overview": {},
  "duration_calculation": {},
  "security_framework": {},
  "business_calendar": {},
  "cache_system": {},
  "gdpr_compliance": {},
  "json_processing": {},
  "database_security": {},
  "protection_systems": {},
  "query_building": {},
  "extracted_files": [],
  "module_statistics": {},
  "security_analysis": {}
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
        
        # Get file size and basic analysis
        local file_size=$(wc -c < "$file_path")
        local line_count=$(wc -l < "$file_path")
        
        # Add to extracted files list with metadata
        jq --arg file "$file_path" --arg key "$content_key" --arg size "$file_size" \
           --arg lines "$line_count" --arg desc "$description" \
           '.extracted_files += [{"file": $file, "content_key": $key, "size": ($size | tonumber), "lines": ($lines | tonumber), "description": $desc, "status": "extracted"}]' \
           "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
        
        return 0
    else
        echo -e "${YELLOW}⚠️ File not found: $file_path${NC}"
        
        # Add to extracted files list as missing
        jq --arg file "$file_path" --arg key "$content_key" --arg desc "$description" \
           '.extracted_files += [{"file": $file, "content_key": $key, "size": 0, "lines": 0, "description": $desc, "status": "missing"}]' \
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
        
        # Extract section content using simple approach
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

# Function to analyze Python file for security patterns
analyze_security_patterns() {
    local file_path="$1"
    local pattern_type="$2"
    
    if [[ -f "$file_path" ]]; then
        echo -e "${PURPLE}🔍 Analyzing security patterns in $(basename "$file_path") (${pattern_type})${NC}"
        
        # Count security-related patterns
        local security_imports=$(grep -c "import.*security\|from.*security" "$file_path" 2>/dev/null || echo "0")
        local crypto_usage=$(grep -c "hashlib\|cryptography\|encrypt\|decrypt" "$file_path" 2>/dev/null || echo "0")
        local validation_patterns=$(grep -c "validate\|sanitize\|escape" "$file_path" 2>/dev/null || echo "0")
        local logging_patterns=$(grep -c "logging\|logger" "$file_path" 2>/dev/null || echo "0")
        
        # Add security analysis to JSON
        jq --arg file "$(basename "$file_path")" --arg security_imports "$security_imports" \
           --arg crypto_usage "$crypto_usage" --arg validation_patterns "$validation_patterns" \
           --arg logging_patterns "$logging_patterns" --arg pattern_type "$pattern_type" \
           '.security_analysis.'"$(basename "$file_path" .py)"' = {"security_imports": ($security_imports | tonumber), "crypto_usage": ($crypto_usage | tonumber), "validation_patterns": ($validation_patterns | tonumber), "logging_patterns": ($logging_patterns | tonumber), "pattern_type": $pattern_type}' \
           "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
        
        echo -e "${GREEN}  ✅ Security analysis: $security_imports security imports, $crypto_usage crypto patterns${NC}"
        return 0
    else
        echo -e "${YELLOW}  ⚠️ File not found for analysis: $file_path${NC}"
        return 1
    fi
}

# Start extraction process
echo -e "${BLUE}📊 Starting duration_system context extraction...${NC}"

# Update timestamp
jq --arg timestamp "$TIMESTAMP" '.extraction_timestamp = $timestamp' "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

# 1. Extract main duration_system/CLAUDE.md
echo -e "\n${PURPLE}📄 Processing Main Module Documentation${NC}"
MAIN_CLAUDE_MD="$DURATION_MODULE/CLAUDE.md"

if extract_file_content "$MAIN_CLAUDE_MD" "main_module_documentation" "Primary duration system documentation"; then
    # Extract key sections from main CLAUDE.md
    extract_markdown_section "$MAIN_CLAUDE_MD" "Duration.*System" "duration_system_overview"
    extract_markdown_section "$MAIN_CLAUDE_MD" "Security.*Framework" "security_framework"
    extract_markdown_section "$MAIN_CLAUDE_MD" "Business.*Calendar" "business_calendar_system"
    extract_markdown_section "$MAIN_CLAUDE_MD" "GDPR.*Compliance" "gdpr_compliance_overview"
    extract_markdown_section "$MAIN_CLAUDE_MD" "Performance.*Optimization" "performance_optimization"
    extract_markdown_section "$MAIN_CLAUDE_MD" "Module.*Architecture" "module_architecture"
fi

# 2. Extract Core Duration Calculation Files
echo -e "\n${PURPLE}⏱️ Processing Duration Calculation Core${NC}"

extract_file_content "$DURATION_MODULE/duration_calculator.py" "duration_calculator" "Core duration calculation engine"
analyze_security_patterns "$DURATION_MODULE/duration_calculator.py" "calculation_engine"

extract_file_content "$DURATION_MODULE/duration_formatter.py" "duration_formatter" "Duration formatting and display utilities"
analyze_security_patterns "$DURATION_MODULE/duration_formatter.py" "formatting_utilities"

extract_file_content "$DURATION_MODULE/business_calendar.py" "business_calendar" "Business day calculation and calendar integration"
analyze_security_patterns "$DURATION_MODULE/business_calendar.py" "calendar_system"

# 3. Extract Security Framework Files
echo -e "\n${PURPLE}🔐 Processing Security Framework${NC}"

extract_file_content "$DURATION_MODULE/secure_database.py" "secure_database" "Database security utilities and protection"
analyze_security_patterns "$DURATION_MODULE/secure_database.py" "database_security"

extract_file_content "$DURATION_MODULE/secure_serialization.py" "secure_serialization" "Safe serialization and deserialization"
analyze_security_patterns "$DURATION_MODULE/secure_serialization.py" "serialization_security"

extract_file_content "$DURATION_MODULE/dos_protection.py" "dos_protection" "Denial of Service protection mechanisms"
analyze_security_patterns "$DURATION_MODULE/dos_protection.py" "dos_protection"

extract_file_content "$DURATION_MODULE/log_sanitization.py" "log_sanitization" "Log sanitization and security utilities"
analyze_security_patterns "$DURATION_MODULE/log_sanitization.py" "log_security"

# 4. Extract JSON Processing Framework
echo -e "\n${PURPLE}📄 Processing JSON Framework${NC}"

extract_file_content "$DURATION_MODULE/json_handler.py" "json_handler" "JSON processing and manipulation utilities"
analyze_security_patterns "$DURATION_MODULE/json_handler.py" "json_processing"

extract_file_content "$DURATION_MODULE/json_security.py" "json_security" "JSON security validation and sanitization"
analyze_security_patterns "$DURATION_MODULE/json_security.py" "json_security"

# 5. Extract GDPR Compliance System
echo -e "\n${PURPLE}⚖️ Processing GDPR Compliance${NC}"

extract_file_content "$DURATION_MODULE/gdpr_compliance.py" "gdpr_compliance" "GDPR compliance framework and utilities"
analyze_security_patterns "$DURATION_MODULE/gdpr_compliance.py" "gdpr_framework"

extract_file_content "$DURATION_MODULE/gdpr_integration.py" "gdpr_integration" "GDPR integration with existing systems"
analyze_security_patterns "$DURATION_MODULE/gdpr_integration.py" "gdpr_integration"

# 6. Extract Database Transaction System
echo -e "\n${PURPLE}🗄️ Processing Database Transaction System${NC}"

extract_file_content "$DURATION_MODULE/database_transactions.py" "database_transactions" "Database transaction management and safety"
analyze_security_patterns "$DURATION_MODULE/database_transactions.py" "transaction_management"

extract_file_content "$DURATION_MODULE/cascade_transactions.py" "cascade_transactions" "Cascading transaction operations"
analyze_security_patterns "$DURATION_MODULE/cascade_transactions.py" "cascade_operations"

extract_file_content "$DURATION_MODULE/query_builders.py" "query_builders" "Safe SQL query building utilities"
analyze_security_patterns "$DURATION_MODULE/query_builders.py" "query_building"

# 7. Extract Performance and Cache System
echo -e "\n${PURPLE}⚡ Processing Performance & Cache System${NC}"

extract_file_content "$DURATION_MODULE/cache_fix.py" "cache_fix" "Cache optimization and consistency fixes"
analyze_security_patterns "$DURATION_MODULE/cache_fix.py" "cache_optimization"

extract_file_content "$DURATION_MODULE/circuit_breaker.py" "circuit_breaker" "Circuit breaker pattern for system resilience"
analyze_security_patterns "$DURATION_MODULE/circuit_breaker.py" "resilience_patterns"

extract_file_content "$DURATION_MODULE/rate_limiter.py" "rate_limiter" "Rate limiting implementation for API protection"
analyze_security_patterns "$DURATION_MODULE/rate_limiter.py" "rate_limiting"

# 8. Extract Migration and Encryption Tools
echo -e "\n${PURPLE}🔄 Processing Migration & Encryption Tools${NC}"

extract_file_content "$DURATION_MODULE/migrate_to_encrypted_databases.py" "encrypted_migration" "Database encryption migration utilities"
analyze_security_patterns "$DURATION_MODULE/migrate_to_encrypted_databases.py" "encryption_migration"

# 9. Module Structure Analysis
echo -e "\n${PURPLE}🏗️ Analyzing Module Structure${NC}"

# Count files by category
CALC_FILES=$(find "$DURATION_MODULE" -name "*duration*" -name "*.py" | wc -l)
SECURITY_FILES=$(find "$DURATION_MODULE" -name "*secure*" -o -name "*gdpr*" -o -name "*protection*" | grep "\.py$" | wc -l)
JSON_FILES=$(find "$DURATION_MODULE" -name "*json*" -name "*.py" | wc -l)
DB_FILES=$(find "$DURATION_MODULE" -name "*database*" -o -name "*transaction*" -o -name "*query*" | grep "\.py$" | wc -l)
CACHE_FILES=$(find "$DURATION_MODULE" -name "*cache*" -o -name "*circuit*" -o -name "*rate*" | grep "\.py$" | wc -l)

# Get total file count and size
TOTAL_PY_FILES=$(find "$DURATION_MODULE" -name "*.py" | wc -l)
TOTAL_SIZE=$(find "$DURATION_MODULE" -name "*.py" -exec wc -c {} + | tail -1 | awk '{print $1}')

jq --arg calc_files "$CALC_FILES" --arg security_files "$SECURITY_FILES" \
   --arg json_files "$JSON_FILES" --arg db_files "$DB_FILES" --arg cache_files "$CACHE_FILES" \
   --arg total_files "$TOTAL_PY_FILES" --arg total_size "$TOTAL_SIZE" \
   '.module_statistics = {"calculation_files": ($calc_files | tonumber), "security_files": ($security_files | tonumber), "json_files": ($json_files | tonumber), "database_files": ($db_files | tonumber), "cache_files": ($cache_files | tonumber), "total_python_files": ($total_files | tonumber), "total_module_size": ($total_size | tonumber)}' \
   "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

# 10. Security Pattern Analysis Summary
echo -e "\n${PURPLE}🔍 Generating Security Analysis Summary${NC}"

# Count total security patterns across all files
TOTAL_SECURITY_IMPORTS=$(find "$DURATION_MODULE" -name "*.py" -exec grep -l "import.*security\|from.*security" {} \; 2>/dev/null | wc -l)
TOTAL_CRYPTO_FILES=$(find "$DURATION_MODULE" -name "*.py" -exec grep -l "hashlib\|cryptography\|encrypt\|decrypt" {} \; 2>/dev/null | wc -l)
TOTAL_VALIDATION_FILES=$(find "$DURATION_MODULE" -name "*.py" -exec grep -l "validate\|sanitize\|escape" {} \; 2>/dev/null | wc -l)

jq --arg security_imports "$TOTAL_SECURITY_IMPORTS" --arg crypto_files "$TOTAL_CRYPTO_FILES" \
   --arg validation_files "$TOTAL_VALIDATION_FILES" \
   '.security_analysis.summary = {"files_with_security_imports": ($security_imports | tonumber), "files_with_crypto": ($crypto_files | tonumber), "files_with_validation": ($validation_files | tonumber)}' \
   "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

# 11. Final Statistics
echo -e "\n${PURPLE}📊 Generating Final Statistics${NC}"

# Count extracted files
EXTRACTED_COUNT=$(jq '.extracted_files | length' "$OUTPUT_FILE")
SUCCESS_COUNT=$(jq '.extracted_files | map(select(.status != "missing")) | length' "$OUTPUT_FILE")
TOTAL_EXTRACTED_SIZE=$(jq '.extracted_files | map(select(.status == "extracted")) | map(.size) | add // 0' "$OUTPUT_FILE")
TOTAL_EXTRACTED_LINES=$(jq '.extracted_files | map(select(.status == "extracted")) | map(.lines) | add // 0' "$OUTPUT_FILE")

# Add extraction summary
jq --arg extracted "$EXTRACTED_COUNT" --arg success "$SUCCESS_COUNT" \
   --arg total_size "$TOTAL_EXTRACTED_SIZE" --arg total_lines "$TOTAL_EXTRACTED_LINES" --arg timestamp "$TIMESTAMP" \
   '.extraction_summary = {"total_files_processed": ($extracted | tonumber), "successful_extractions": ($success | tonumber), "total_extracted_size": ($total_size | tonumber), "total_extracted_lines": ($total_lines | tonumber), "completion_timestamp": $timestamp}' \
   "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

# Validation and final output
echo -e "\n${GREEN}✅ Duration system context extraction completed!${NC}"
echo "=============================================="
echo -e "${PURPLE}📊 Extraction Summary:${NC}"
echo "  • Files processed: $EXTRACTED_COUNT"
echo "  • Successful extractions: $SUCCESS_COUNT"
echo "  • Total extracted size: $(numfmt --to=iec $TOTAL_EXTRACTED_SIZE 2>/dev/null || echo "$TOTAL_EXTRACTED_SIZE") bytes"
echo "  • Total extracted lines: $TOTAL_EXTRACTED_LINES"
echo "  • Output file: $OUTPUT_FILE"
echo "  • Output size: $(du -h "$OUTPUT_FILE" | cut -f1)"

# Validate JSON format
if jq empty "$OUTPUT_FILE" 2>/dev/null; then
    echo -e "${GREEN}  ✅ JSON format valid${NC}"
else
    echo -e "${RED}  ❌ JSON format invalid${NC}"
    exit 1
fi

# Display security analysis
echo -e "\n${PURPLE}🔍 Security Analysis Results:${NC}"
echo "  • Files with security imports: $TOTAL_SECURITY_IMPORTS"
echo "  • Files with cryptography: $TOTAL_CRYPTO_FILES"
echo "  • Files with validation: $TOTAL_VALIDATION_FILES"

# Display module categorization
echo -e "\n${PURPLE}🏗️ Module Categorization:${NC}"
echo "  • Calculation files: $CALC_FILES"
echo "  • Security files: $SECURITY_FILES"
echo "  • JSON processing files: $JSON_FILES"
echo "  • Database files: $DB_FILES"
echo "  • Cache/Performance files: $CACHE_FILES"

echo -e "\n${GREEN}🏆 Duration system context extraction completed successfully!${NC}"
echo "Ready for systematic file auditor integration."
echo ""

# Optional: Display context file for verification
if [[ "${2:-}" == "--show" ]]; then
    echo -e "${PURPLE}📄 Generated Context (first 50 lines):${NC}"
    echo "----------------------------------------"
    head -50 "$OUTPUT_FILE"
    echo "----------------------------------------"
fi

exit 0