#!/bin/bash

# ⏱️ CONTEXT EXTRACTION SCRIPT - DURATION SYSTEM MODULE (SIMPLIFIED)
# Purpose: Extract comprehensive context from duration_system module for systematic file auditor
# Created: 2025-08-19 (Sétima Camada - Context Extraction System)
# Usage: ./context_duration_simple.sh [output_file]

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

echo -e "${PURPLE}⏱️ DURATION SYSTEM CONTEXT EXTRACTION (SIMPLIFIED)${NC}"
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

# Start extraction process
echo -e "${BLUE}📊 Starting duration_system context extraction...${NC}"

# Update timestamp
jq --arg timestamp "$TIMESTAMP" '.extraction_timestamp = $timestamp' "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

# 1. Extract main duration_system/CLAUDE.md
echo -e "\n${PURPLE}📄 Processing Main Module Documentation${NC}"
extract_file_content "$DURATION_MODULE/CLAUDE.md" "main_module_documentation" "Primary duration system documentation"

# 2. Extract Core Duration Calculation Files
echo -e "\n${PURPLE}⏱️ Processing Duration Calculation Core${NC}"
extract_file_content "$DURATION_MODULE/duration_calculator.py" "duration_calculator" "Core duration calculation engine"
extract_file_content "$DURATION_MODULE/duration_formatter.py" "duration_formatter" "Duration formatting and display utilities"
extract_file_content "$DURATION_MODULE/business_calendar.py" "business_calendar" "Business day calculation and calendar integration"

# 3. Extract Security Framework Files
echo -e "\n${PURPLE}🔐 Processing Security Framework${NC}"
extract_file_content "$DURATION_MODULE/secure_database.py" "secure_database" "Database security utilities and protection"
extract_file_content "$DURATION_MODULE/secure_serialization.py" "secure_serialization" "Safe serialization and deserialization"
extract_file_content "$DURATION_MODULE/dos_protection.py" "dos_protection" "Denial of Service protection mechanisms"
extract_file_content "$DURATION_MODULE/log_sanitization.py" "log_sanitization" "Log sanitization and security utilities"

# 4. Extract JSON Processing Framework
echo -e "\n${PURPLE}📄 Processing JSON Framework${NC}"
extract_file_content "$DURATION_MODULE/json_handler.py" "json_handler" "JSON processing and manipulation utilities"
extract_file_content "$DURATION_MODULE/json_security.py" "json_security" "JSON security validation and sanitization"

# 5. Extract GDPR Compliance System
echo -e "\n${PURPLE}⚖️ Processing GDPR Compliance${NC}"
extract_file_content "$DURATION_MODULE/gdpr_compliance.py" "gdpr_compliance" "GDPR compliance framework and utilities"
extract_file_content "$DURATION_MODULE/gdpr_integration.py" "gdpr_integration" "GDPR integration with existing systems"

# 6. Extract Database Transaction System
echo -e "\n${PURPLE}🗄️ Processing Database Transaction System${NC}"
extract_file_content "$DURATION_MODULE/database_transactions.py" "database_transactions" "Database transaction management and safety"
extract_file_content "$DURATION_MODULE/cascade_transactions.py" "cascade_transactions" "Cascading transaction operations"
extract_file_content "$DURATION_MODULE/query_builders.py" "query_builders" "Safe SQL query building utilities"

# 7. Extract Performance and Cache System
echo -e "\n${PURPLE}⚡ Processing Performance & Cache System${NC}"
extract_file_content "$DURATION_MODULE/cache_fix.py" "cache_fix" "Cache optimization and consistency fixes"
extract_file_content "$DURATION_MODULE/circuit_breaker.py" "circuit_breaker" "Circuit breaker pattern for system resilience"
extract_file_content "$DURATION_MODULE/rate_limiter.py" "rate_limiter" "Rate limiting implementation for API protection"

# 8. Extract Migration and Encryption Tools
echo -e "\n${PURPLE}🔄 Processing Migration & Encryption Tools${NC}"
extract_file_content "$DURATION_MODULE/migrate_to_encrypted_databases.py" "encrypted_migration" "Database encryption migration utilities"

echo -e "\n${PURPLE}📊 Generating Module Statistics${NC}"

# Module Structure Analysis - Simple approach
TOTAL_PY_FILES=$(find "$DURATION_MODULE" -name "*.py" 2>/dev/null | wc -l || echo "0")
TOTAL_SIZE=$(find "$DURATION_MODULE" -name "*.py" -exec wc -c {} + 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")

jq --arg total_files "$TOTAL_PY_FILES" --arg total_size "$TOTAL_SIZE" \
   '.module_statistics = {"total_python_files": ($total_files | tonumber), "total_module_size": ($total_size | tonumber)}' \
   "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

echo -e "\n${PURPLE}🔍 Generating Security Analysis${NC}"

# Security Pattern Analysis - Simple approach
SECURITY_FILES=$(find "$DURATION_MODULE" -name "*secure*" -o -name "*gdpr*" -o -name "*protection*" 2>/dev/null | grep "\.py$" | wc -l || echo "0")
JSON_FILES=$(find "$DURATION_MODULE" -name "*json*" 2>/dev/null | grep "\.py$" | wc -l || echo "0")

jq --arg security_files "$SECURITY_FILES" --arg json_files "$JSON_FILES" \
   '.security_analysis = {"security_files": ($security_files | tonumber), "json_files": ($json_files | tonumber)}' \
   "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp" && mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

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

echo -e "\n${GREEN}🏆 Duration system context extraction completed successfully!${NC}"
echo "Ready for systematic file auditor integration."
echo ""

exit 0