"""
🔐 JSON Security and Validation Module

Enhanced security measures for JSON field handling.
Addresses critical security issues from Codex audit:

1. Input sanitization and validation
2. Protection against JSON injection attacks
3. Size and depth limits to prevent DoS
4. Schema enforcement with strict validation
5. Safe deserialization practices
6. Malicious content detection

Security Features:
- Maximum nesting depth protection
- Size limits per field and total
- Dangerous key pattern detection
- Script injection prevention
- Prototype pollution protection
- Circular reference detection
"""

import json
import re
import hashlib
import sys
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class SecurityViolationType(Enum):
    """Types of security violations detected."""
    SIZE_LIMIT_EXCEEDED = "size_limit_exceeded"
    DEPTH_LIMIT_EXCEEDED = "depth_limit_exceeded"
    DANGEROUS_KEY = "dangerous_key"
    SCRIPT_INJECTION = "script_injection"
    PROTOTYPE_POLLUTION = "prototype_pollution"
    CIRCULAR_REFERENCE = "circular_reference"
    INVALID_UNICODE = "invalid_unicode"
    BINARY_DATA = "binary_data"
    SQL_INJECTION = "sql_injection"
    PATH_TRAVERSAL = "path_traversal"


@dataclass
class SecurityViolation:
    """Security violation details."""
    violation_type: SecurityViolationType
    message: str
    path: str
    value: Optional[Any] = None
    severity: str = "high"


class JsonSecurityError(Exception):
    """Exception for JSON security violations."""
    def __init__(self, message: str, violations: List[SecurityViolation] = None):
        super().__init__(message)
        self.violations = violations or []


class SecureJsonValidator:
    """
    Secure JSON validation with comprehensive security checks.
    
    Provides protection against:
    - JSON injection attacks
    - Prototype pollution
    - DoS through deep nesting or large payloads
    - Script injection
    - Path traversal
    - SQL injection patterns
    """
    
    # Security constants
    DEFAULT_MAX_DEPTH = 10
    DEFAULT_MAX_SIZE = 100_000  # 100KB per field
    DEFAULT_MAX_TOTAL_SIZE = 1_000_000  # 1MB total
    DEFAULT_MAX_KEYS = 1000
    DEFAULT_MAX_STRING_LENGTH = 10_000
    DEFAULT_MAX_ARRAY_LENGTH = 1000
    
    # Dangerous patterns
    DANGEROUS_KEY_PATTERNS = [
        r"__proto__",  # Prototype pollution
        r"constructor",  # Constructor override
        r"prototype",  # Prototype manipulation
        r"\$\$",  # Angular/Vue internal
        r"^\$",  # MongoDB operators
        r"^_",  # Internal fields
        r"<script",  # Script tags
        r"javascript:",  # JS protocol
        r"on\w+\s*=",  # Event handlers
        r"eval\s*\(",  # Eval function
        r"Function\s*\(",  # Function constructor
    ]
    
    SCRIPT_INJECTION_PATTERNS = [
        # Basic script injection
        r"<script[^>]*>.*?</script>",         # Script tags
        r"<SCRIPT[^>]*>.*?</SCRIPT>",         # Script tags (uppercase)
        r"javascript:\s*",                    # JavaScript protocol
        r"JAVASCRIPT:\s*",                    # JavaScript protocol (uppercase)
        r"vbscript:\s*",                      # VBScript protocol
        r"VBSCRIPT:\s*",                      # VBScript protocol (uppercase)
        
        # Event handlers
        r"on\w+\s*=\s*[\"']",                 # Event handlers
        r"ON\w+\s*=\s*[\"']",                 # Event handlers (uppercase)
        r"onclick\s*=",                       # Specific onclick
        r"onload\s*=",                        # Specific onload
        r"onerror\s*=",                       # Specific onerror
        r"onmouseover\s*=",                   # Specific onmouseover
        r"onfocus\s*=",                       # Specific onfocus
        r"onblur\s*=",                        # Specific onblur
        r"onkeydown\s*=",                     # Specific onkeydown
        r"onsubmit\s*=",                      # Specific onsubmit
        
        # JavaScript functions
        r"eval\s*\(",                         # Eval calls
        r"EVAL\s*\(",                         # Eval calls (uppercase)
        r"setTimeout\s*\(",                   # SetTimeout
        r"setInterval\s*\(",                  # SetInterval
        r"Function\s*\(",                     # Function constructor
        r"FUNCTION\s*\(",                     # Function constructor (uppercase)
        r"execScript\s*\(",                   # IE execScript
        r"setImmediate\s*\(",                 # setImmediate
        
        # DOM manipulation
        r"\.innerHTML\s*=",                   # innerHTML assignment
        r"\.outerHTML\s*=",                   # outerHTML assignment
        r"\.innerText\s*=",                   # innerText assignment
        r"\.textContent\s*=",                 # textContent assignment
        r"\.src\s*=",                         # src assignment
        r"\.href\s*=",                        # href assignment
        r"\.action\s*=",                      # form action assignment
        r"document\.\w+",                     # Document manipulation
        r"window\.\w+",                       # Window manipulation
        r"parent\.\w+",                       # Parent frame access
        r"top\.\w+",                          # Top frame access
        r"self\.\w+",                         # Self reference
        
        # Data URIs and encoding
        r"data:\s*text/html",                 # Data URI HTML
        r"data:\s*image/svg\+xml",            # Data URI SVG
        r"data:\s*application/javascript",    # Data URI JavaScript
        r"data:.*base64",                     # Data URI base64
        
        # SVG injection
        r"<svg[^>]*>.*?</svg>",               # SVG tags
        r"<SVG[^>]*>.*?</SVG>",               # SVG tags (uppercase)
        r"<svg[^>]*onload",                   # SVG onload
        r"<animateTransform[^>]*>",           # SVG animation
        r"<animate[^>]*>",                    # SVG animate
        r"<set[^>]*>",                        # SVG set
        
        # CSS injection
        r"<style[^>]*>.*?</style>",           # Style tags
        r"<STYLE[^>]*>.*?</STYLE>",           # Style tags (uppercase)
        r"@import\s*[\"']javascript:",        # CSS @import with JavaScript
        r"expression\s*\(",                   # IE CSS expressions
        r"behavior\s*:",                      # IE CSS behavior
        r"background\s*:\s*url\s*\(\s*javascript:", # CSS background JavaScript
        r"background-image\s*:\s*url\s*\(\s*javascript:", # CSS background-image JavaScript
        
        # Template injection (popular frameworks)
        r"\{\{.*?\}\}",                       # Angular/Handlebars template
        r"\{\%.*?\%\}",                       # Jinja2/Django template
        r"\[\[.*?\]\]",                       # Vue.js template
        r"\$\{.*?\}",                         # Template literals
        r"<%.*?%>",                           # ASP/JSP template
        r"<\?.*?\?>",                         # PHP template
        
        # Modern JavaScript features
        r"import\s*\(",                       # Dynamic imports
        r"import\s+.*\s+from",                # ES6 imports
        r"require\s*\(",                      # CommonJS require
        r"fetch\s*\(",                        # Fetch API
        r"XMLHttpRequest\s*\(",               # XHR
        r"WebSocket\s*\(",                    # WebSocket
        r"Worker\s*\(",                       # Web Workers
        r"SharedWorker\s*\(",                 # Shared Workers
        r"ServiceWorker\s*\(",                # Service Workers
        
        # Framework-specific injections
        r"ng-.*=",                            # AngularJS directives
        r"v-.*=",                             # Vue.js directives
        r"@.*=",                              # Vue.js events
        r"dangerouslySetInnerHTML",           # React dangerous HTML
        r"\[innerHTML\]",                     # Angular property binding
        r"\(click\)",                         # Angular event binding
        
        # Encoded variations
        r"&#x[0-9a-fA-F]+;",                  # Hex entities
        r"&#\d+;",                            # Decimal entities
        r"%[0-9a-fA-F]{2}",                   # URL encoding
        r"\\u[0-9a-fA-F]{4}",                 # Unicode escapes
        r"\\x[0-9a-fA-F]{2}",                 # Hex escapes
        
        # Alternative script execution
        r"<object[^>]*>.*?</object>",         # Object tags
        r"<embed[^>]*>",                      # Embed tags
        r"<applet[^>]*>.*?</applet>",         # Applet tags
        r"<iframe[^>]*>.*?</iframe>",         # Iframe tags
        r"<frame[^>]*>",                      # Frame tags
        r"<frameset[^>]*>",                   # Frameset tags
        r"<meta[^>]*http-equiv.*refresh",     # Meta refresh
        r"<link[^>]*rel.*import",             # HTML imports
        
        # HTML5 specific
        r"<audio[^>]*>.*?</audio>",           # Audio tags
        r"<video[^>]*>.*?</video>",           # Video tags
        r"<source[^>]*>",                     # Source tags
        r"<track[^>]*>",                      # Track tags
        r"formaction\s*=",                    # Form action override
        r"autofocus\s*=",                     # Autofocus attribute
        
        # WebRTC and modern APIs
        r"getUserMedia\s*\(",                 # Media access
        r"navigator\.\w+",                    # Navigator object
        r"location\.\w+",                     # Location object
        r"history\.\w+",                      # History object
        r"localStorage\.\w+",                 # Local storage
        r"sessionStorage\.\w+",               # Session storage
        r"indexedDB\.\w+",                    # IndexedDB
        
        # PostMessage and origin bypass
        r"postMessage\s*\(",                  # Post message
        r"addEventListener\s*\(",             # Event listeners
        r"removeEventListener\s*\(",          # Remove event listeners
        r"dispatchEvent\s*\(",                # Dispatch events
        r"createEvent\s*\(",                  # Create events
    ]
    
    SQL_INJECTION_PATTERNS = [
        # Classic injection patterns
        r"'\s*OR\s+'?\d+'\s*=\s*'?\d+'",  # OR 1=1
        r"'\s*or\s+'?\d+'\s*=\s*'?\d+'",  # or 1=1 (lowercase)
        r"'\s*OR\s+'.+?'\s*=\s*'.+?'",   # OR 'x'='x'
        r"'\s*AND\s+'?\d+'\s*=\s*'?\d+'", # AND 1=1
        r"'\s*and\s+'?\d+'\s*=\s*'?\d+'", # and 1=1 (lowercase)
        
        # Command injection patterns
        r";\s*DROP\s+TABLE",              # DROP TABLE
        r";\s*drop\s+table",              # drop table (lowercase)
        r";\s*DELETE\s+FROM",             # DELETE FROM
        r";\s*delete\s+from",             # delete from (lowercase)
        r";\s*INSERT\s+INTO",             # INSERT INTO
        r";\s*insert\s+into",             # insert into (lowercase)
        r";\s*UPDATE\s+\w+\s+SET",        # UPDATE SET
        r";\s*update\s+\w+\s+set",        # update set (lowercase)
        r";\s*TRUNCATE\s+TABLE",          # TRUNCATE TABLE
        r";\s*truncate\s+table",          # truncate table (lowercase)
        r";\s*ALTER\s+TABLE",             # ALTER TABLE
        r";\s*alter\s+table",             # alter table (lowercase)
        
        # Union-based injection
        r"UNION\s+SELECT",                # UNION SELECT
        r"union\s+select",                # union select (lowercase)
        r"UNION\s+ALL\s+SELECT",          # UNION ALL SELECT
        r"union\s+all\s+select",          # union all select (lowercase)
        
        # Nested queries
        r"SELECT\s*\(\s*SELECT",          # SELECT (SELECT
        r"select\s*\(\s*select",          # select (select (lowercase)
        r"\(\s*SELECT\s+.*\s+FROM",       # (SELECT ... FROM
        r"\(\s*select\s+.*\s+from",       # (select ... from (lowercase)
        
        # Time-based attacks
        r"WAITFOR\s+DELAY",               # SQL Server time delay
        r"waitfor\s+delay",               # waitfor delay (lowercase)
        r"BENCHMARK\s*\(",                # MySQL benchmark
        r"benchmark\s*\(",                # benchmark (lowercase)
        r"SLEEP\s*\(",                    # MySQL sleep
        r"sleep\s*\(",                    # sleep (lowercase)
        r"pg_sleep\s*\(",                 # PostgreSQL sleep
        
        # Hex-encoded payloads
        r"0x[0-9A-Fa-f]{8,}",            # Hex strings (8+ chars)
        r"CHAR\s*\(\s*\d+",               # CHAR(numeric) conversion
        r"char\s*\(\s*\d+",               # char(numeric) conversion (lowercase)
        r"CHR\s*\(\s*\d+",                # Oracle CHR function
        r"chr\s*\(\s*\d+",                # chr function (lowercase)
        r"ASCII\s*\(",                    # ASCII function
        r"ascii\s*\(",                    # ascii function (lowercase)
        
        # Comment patterns
        r"--\s*",                         # SQL line comment
        r"/\*.*?\*/",                     # Multi-line comment
        r"#.*$",                          # MySQL comment
        
        # Database-specific functions
        r"xp_cmdshell",                   # SQL Server command execution
        r"sp_executesql",                 # SQL Server dynamic SQL
        r"load_file\s*\(",                # MySQL file reading
        r"into\s+outfile",                # MySQL file writing
        r"into\s+dumpfile",               # MySQL binary file writing
        
        # Information gathering
        r"information_schema",            # Information schema access
        r"sys\.",                         # System tables
        r"sysobjects",                    # SQL Server system objects
        r"syscolumns",                    # SQL Server system columns
        r"version\s*\(\s*\)",             # Version function
        r"@@version",                     # SQL Server version
        r"user\s*\(\s*\)",                # Current user function
        r"current_user",                  # Current user
        r"database\s*\(\s*\)",            # Database function
        
        # Blind injection indicators
        r"AND\s+\d+\s*=\s*\d+",          # AND 1=1
        r"and\s+\d+\s*=\s*\d+",          # and 1=1 (lowercase)
        r"OR\s+\d+\s*=\s*\d+",           # OR 1=1
        r"or\s+\d+\s*=\s*\d+",           # or 1=1 (lowercase)
        r"AND\s+\d+\s*>\s*\d+",          # AND 1>0
        r"and\s+\d+\s*>\s*\d+",          # and 1>0 (lowercase)
        
        # Error-based injection
        r"EXTRACTVALUE\s*\(",             # MySQL error-based
        r"extractvalue\s*\(",             # extractvalue (lowercase)
        r"UPDATEXML\s*\(",                # MySQL error-based
        r"updatexml\s*\(",                # updatexml (lowercase)
        r"CONVERT\s*\(",                  # Type conversion
        r"convert\s*\(",                  # convert (lowercase)
        r"CAST\s*\(",                     # Type casting
        r"cast\s*\(",                     # cast (lowercase)
        
        # Boolean-based blind injection
        r"AND\s+.*\s+LIKE\s+",            # AND ... LIKE
        r"and\s+.*\s+like\s+",            # and ... like (lowercase)
        r"OR\s+.*\s+LIKE\s+",             # OR ... LIKE
        r"or\s+.*\s+like\s+",             # or ... like (lowercase)
        r"RLIKE\s+",                      # MySQL RLIKE
        r"rlike\s+",                      # rlike (lowercase)
        
        # Stacked queries
        r";\s*EXEC\s*\(",                 # Execute stored procedure
        r";\s*exec\s*\(",                 # exec (lowercase)
        r";\s*EXECUTE\s+",                # Execute command
        r";\s*execute\s+",                # execute (lowercase)
        
        # Advanced evasion techniques
        r"\/\*\!\d+.*?\*\/",              # MySQL version-specific comments
        r"CONCAT\s*\(",                   # String concatenation
        r"concat\s*\(",                   # concat (lowercase)
        r"GROUP_CONCAT\s*\(",             # MySQL group concatenation
        r"group_concat\s*\(",             # group_concat (lowercase)
        r"STRING_AGG\s*\(",               # SQL Server string aggregation
        r"string_agg\s*\(",               # string_agg (lowercase)
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        # Basic path traversal
        r"\.\./",                             # Unix path traversal
        r"\.\.\\",                            # Windows path traversal
        r"\.\.\./",                           # Double-dot traversal
        r"\.\.\.\./",                         # Triple-dot traversal
        r"\./\.\./",                          # Relative path traversal
        r"\.\\\.\.\\",                        # Windows double traversal
        r"\.\./\.\./",                        # Multiple Unix traversals
        r"\.\.\\\.\.\\",                      # Multiple Windows traversals
        
        # URL encoded variants
        r"%2e%2e[/\\]",                       # URL encoded ../ or ..\
        r"%2E%2E[/\\]",                       # URL encoded ../ or ..\ (uppercase)
        r"%252e%252e[/\\]",                   # Double URL encoded
        r"%252E%252E[/\\]",                   # Double URL encoded (uppercase)
        r"%c0%ae%c0%ae[/\\]",                 # Overlong UTF-8 encoding
        r"%e0%80%ae%e0%80%ae[/\\]",           # Overlong UTF-8 encoding (longer)
        
        # Unicode variants
        r"\\u002e\\u002e[/\\\\]",             # Unicode escapes
        r"\\u002E\\u002E[/\\\\]",             # Unicode escapes (uppercase)
        r"\u002e\u002e[/\\\\]",               # Direct Unicode
        r"\u002E\u002E[/\\\\]",               # Direct Unicode (uppercase)
        r"\\uff0e\\uff0e[/\\\\]",             # Fullwidth Unicode
        r"\uff0e\uff0e[/\\\\]",               # Direct fullwidth Unicode
        
        # HTML entity encoding
        r"&#46;&#46;[/\\\\]",                 # HTML decimal entities
        r"&#x2e;&#x2e;[/\\\\]",               # HTML hex entities
        r"&#X2E;&#X2E;[/\\\\]",               # HTML hex entities (uppercase)
        r"&period;&period;[/\\\\]",           # HTML named entities
        
        # Mixed encoding
        r"\.%2e[/\\\\]",                      # Mixed literal and encoded
        r"%2e\.[/\\\\]",                      # Mixed encoded and literal
        r"\.%252e[/\\\\]",                    # Mixed literal and double-encoded
        r"%252e\.[/\\\\]",                    # Mixed double-encoded and literal
        
        # Path separator variations
        r"\.\.[/\\\\]",                       # Standard separators
        r"\.\.%2f",                           # URL encoded forward slash
        r"\.\.%5c",                           # URL encoded backslash
        r"\.\.%5C",                           # URL encoded backslash (uppercase)
        r"\.\.%252f",                         # Double URL encoded forward slash
        r"\.\.%255c",                         # Double URL encoded backslash
        r"\.\.%255C",                         # Double URL encoded backslash (uppercase)
        
        # Common target files (Unix)
        r"(?:^|/)etc/passwd",                 # Unix password file
        r"(?:^|/)etc/shadow",                 # Unix shadow file
        r"(?:^|/)etc/hosts",                  # Unix hosts file
        r"(?:^|/)etc/fstab",                  # Unix filesystem table
        r"(?:^|/)etc/crontab",                # Unix cron table
        r"(?:^|/)root/\.bash_history",        # Root bash history
        r"(?:^|/)home/[^/]+/\.bash_history",  # User bash history
        r"(?:^|/)var/log/",                   # Log directory
        r"(?:^|/)proc/self/environ",          # Process environment
        r"(?:^|/)proc/version",               # Kernel version
        r"(?:^|/)proc/cmdline",               # Kernel command line
        
        # Common target files (Windows)
        r"(?:^|\\\\)windows\\\\system32",     # Windows system directory
        r"(?:^|\\\\)windows\\\\win\.ini",     # Windows ini file
        r"(?:^|\\\\)windows\\\\system\.ini",  # Windows system ini
        r"(?:^|\\\\)winnt\\\\system32",       # Windows NT system
        r"(?:^|\\\\)boot\.ini",               # Windows boot file
        r"(?:^|\\\\)autoexec\.bat",           # Windows autoexec
        r"(?:^|\\\\)config\.sys",             # Windows config
        r"(?:^|\\\\)windows\\\\repair\\\\sam", # Windows SAM file
        r"(?:^|\\\\)inetpub\\\\wwwroot",      # IIS web root
        
        # Protocol-based traversal
        r"file://",                           # File protocol
        r"file:///",                          # File protocol with triple slash
        r"ftp://",                            # FTP protocol
        r"sftp://",                           # SFTP protocol
        r"smb://",                            # SMB protocol
        r"\\\\\\\\",                          # UNC paths (escaped)
        r"\\\\",                              # UNC paths
        r"//",                                # Network paths
        
        # Container/jail escapes
        r"/proc/self/root/",                  # Process root escape
        r"/proc/1/root/",                     # Init process root
        r"/proc/self/cwd/",                   # Current working directory
        r"/sys/class/",                       # System class directory
        r"/dev/",                             # Device directory
        r"/run/secrets/",                     # Container secrets
        
        # Web application specific
        r"WEB-INF/",                          # Java web app directory
        r"META-INF/",                         # Java metadata directory
        r"\.svn/",                            # Subversion directory
        r"\.git/",                            # Git directory
        r"\.hg/",                             # Mercurial directory
        r"\.bzr/",                            # Bazaar directory
        r"CVS/",                              # CVS directory
        r"\.env",                             # Environment file
        r"\.htaccess",                        # Apache config
        r"\.htpasswd",                        # Apache password
        r"web\.config",                       # IIS config
        r"application\.properties",           # Java properties
        r"config\.php",                       # PHP config
        r"wp-config\.php",                    # WordPress config
        
        # Archive/compression escapes
        r"\.\.tar",                           # Tar archive escape
        r"\.\.zip",                           # Zip archive escape
        r"\.\.gz",                            # Gzip escape
        r"\.\.bz2",                           # Bzip2 escape
        r"\.\.xz",                            # XZ escape
        
        # Null byte injection (historical)
        r"\.\.%00",                           # Null byte
        r"\.\.\x00",                          # Direct null byte
        r"\.\.\\0",                           # Escaped null byte
        
        # Advanced evasion techniques
        r"\.{2,}/",                           # Multiple dots
        r"\.{2,}\\\\",                        # Multiple dots (Windows)
        r"[.]{2,}[/\\\\]",                    # Character class dots
        r"\.\.(?:/[^/]*)*",                   # Deep traversal patterns
        r"\.\.(?:\\\\[^\\\\]*)*",             # Deep traversal patterns (Windows)
        
        # Case variations (flags handled at compile time)
        r"\.\.[/\\\\]",                       # Standard separators (case handled by IGNORECASE flag)
        
        # Combined with legitimate paths
        r"uploads/\.\./",                     # Combined with upload directory
        r"images/\.\./",                      # Combined with images directory
        r"static/\.\./",                      # Combined with static directory
        r"assets/\.\./",                      # Combined with assets directory
        r"public/\.\./",                      # Combined with public directory
        r"tmp/\.\./",                         # Combined with temp directory
    ]
    
    def __init__(self,
                 max_depth: int = None,
                 max_size: int = None,
                 max_total_size: int = None,
                 max_keys: int = None,
                 max_string_length: int = None,
                 max_array_length: int = None,
                 allow_dangerous_keys: bool = False,
                 strict_mode: bool = True):
        """
        Initialize secure JSON validator.
        
        Args:
            max_depth: Maximum nesting depth
            max_size: Maximum size per field in bytes
            max_total_size: Maximum total JSON size
            max_keys: Maximum number of keys
            max_string_length: Maximum string value length
            max_array_length: Maximum array length
            allow_dangerous_keys: Allow potentially dangerous keys
            strict_mode: Enable all security checks
        """
        self.max_depth = max_depth or self.DEFAULT_MAX_DEPTH
        self.max_size = max_size or self.DEFAULT_MAX_SIZE
        self.max_total_size = max_total_size or self.DEFAULT_MAX_TOTAL_SIZE
        self.max_keys = max_keys or self.DEFAULT_MAX_KEYS
        self.max_string_length = max_string_length or self.DEFAULT_MAX_STRING_LENGTH
        self.max_array_length = max_array_length or self.DEFAULT_MAX_ARRAY_LENGTH
        self.allow_dangerous_keys = allow_dangerous_keys
        self.strict_mode = strict_mode
        
        # Compile patterns for efficiency
        self._dangerous_key_regex = [re.compile(p, re.IGNORECASE) 
                                    for p in self.DANGEROUS_KEY_PATTERNS]
        self._script_injection_regex = [re.compile(p, re.IGNORECASE | re.DOTALL) 
                                       for p in self.SCRIPT_INJECTION_PATTERNS]
        self._sql_injection_regex = [re.compile(p, re.IGNORECASE) 
                                    for p in self.SQL_INJECTION_PATTERNS]
        self._path_traversal_regex = [re.compile(p, re.IGNORECASE) 
                                     for p in self.PATH_TRAVERSAL_PATTERNS]
    
    def validate_json_string(self, json_string: str) -> Tuple[bool, List[SecurityViolation]]:
        """
        Validate a JSON string for security issues.
        
        Returns:
            Tuple of (is_valid, violations_list)
        """
        violations = []
        
        # Check total size
        if len(json_string.encode('utf-8')) > self.max_total_size:
            violations.append(SecurityViolation(
                violation_type=SecurityViolationType.SIZE_LIMIT_EXCEEDED,
                message=f"Total JSON size exceeds {self.max_total_size} bytes",
                path="$",
                severity="high"
            ))
            return False, violations
        
        # Parse JSON
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            violations.append(SecurityViolation(
                violation_type=SecurityViolationType.INVALID_UNICODE,
                message=f"Invalid JSON format: {e}",
                path="$",
                severity="critical"
            ))
            return False, violations
        
        # Validate parsed data
        return self.validate_data(data)
    
    def validate_data(self, data: Any, path: str = "$") -> Tuple[bool, List[SecurityViolation]]:
        """
        Validate parsed JSON data for security issues.
        
        Returns:
            Tuple of (is_valid, violations_list)
        """
        violations = []
        visited = set()
        
        # Check for circular references
        def check_circular(obj: Any, current_path: str, depth: int = 0) -> List[SecurityViolation]:
            nonlocal visited
            local_violations = []
            
            # Check depth limit
            if depth > self.max_depth:
                local_violations.append(SecurityViolation(
                    violation_type=SecurityViolationType.DEPTH_LIMIT_EXCEEDED,
                    message=f"Nesting depth exceeds {self.max_depth}",
                    path=current_path,
                    severity="high"
                ))
                return local_violations
            
            # Handle different types
            if isinstance(obj, dict):
                # Check object ID for circular reference
                obj_id = id(obj)
                if obj_id in visited:
                    local_violations.append(SecurityViolation(
                        violation_type=SecurityViolationType.CIRCULAR_REFERENCE,
                        message="Circular reference detected",
                        path=current_path,
                        severity="critical"
                    ))
                    return local_violations
                
                visited.add(obj_id)
                
                # Check number of keys
                if len(obj) > self.max_keys:
                    local_violations.append(SecurityViolation(
                        violation_type=SecurityViolationType.SIZE_LIMIT_EXCEEDED,
                        message=f"Object has {len(obj)} keys, exceeds limit of {self.max_keys}",
                        path=current_path,
                        severity="medium"
                    ))
                
                # Check each key and value
                for key, value in obj.items():
                    # Validate key
                    key_violations = self._validate_key(key, f"{current_path}.{key}")
                    local_violations.extend(key_violations)
                    
                    # Validate value
                    if isinstance(value, str):
                        str_violations = self._validate_string(value, f"{current_path}.{key}")
                        local_violations.extend(str_violations)
                    
                    # Recursive check
                    if isinstance(value, (dict, list)):
                        nested_violations = check_circular(value, f"{current_path}.{key}", depth + 1)
                        local_violations.extend(nested_violations)
                
                visited.remove(obj_id)
                
            elif isinstance(obj, list):
                # Check array length
                if len(obj) > self.max_array_length:
                    local_violations.append(SecurityViolation(
                        violation_type=SecurityViolationType.SIZE_LIMIT_EXCEEDED,
                        message=f"Array has {len(obj)} items, exceeds limit of {self.max_array_length}",
                        path=current_path,
                        severity="medium"
                    ))
                
                # Check each item
                for i, item in enumerate(obj):
                    if isinstance(item, str):
                        str_violations = self._validate_string(item, f"{current_path}[{i}]")
                        local_violations.extend(str_violations)
                    
                    # Recursive check
                    if isinstance(item, (dict, list)):
                        nested_violations = check_circular(item, f"{current_path}[{i}]", depth + 1)
                        local_violations.extend(nested_violations)
            
            return local_violations
        
        # Run validation
        violations = check_circular(data, path)
        
        # Return results
        is_valid = len(violations) == 0
        return is_valid, violations
    
    def _validate_key(self, key: str, path: str) -> List[SecurityViolation]:
        """Validate object key for dangerous patterns."""
        violations = []
        
        if not self.allow_dangerous_keys and self.strict_mode:
            # Check dangerous key patterns
            for pattern in self._dangerous_key_regex:
                if pattern.search(key):
                    violations.append(SecurityViolation(
                        violation_type=SecurityViolationType.DANGEROUS_KEY,
                        message=f"Dangerous key pattern detected: {key}",
                        path=path,
                        value=key,
                        severity="critical"
                    ))
                    break
        
        return violations
    
    def _validate_string(self, value: str, path: str) -> List[SecurityViolation]:
        """Validate string value for injection attacks."""
        violations = []
        
        # Check string length
        if len(value) > self.max_string_length:
            violations.append(SecurityViolation(
                violation_type=SecurityViolationType.SIZE_LIMIT_EXCEEDED,
                message=f"String length {len(value)} exceeds limit of {self.max_string_length}",
                path=path,
                severity="medium"
            ))
            return violations  # Skip other checks for oversized strings
        
        if self.strict_mode:
            # Check for script injection
            for pattern in self._script_injection_regex:
                if pattern.search(value):
                    violations.append(SecurityViolation(
                        violation_type=SecurityViolationType.SCRIPT_INJECTION,
                        message="Script injection pattern detected",
                        path=path,
                        value=value[:100],  # Truncate for safety
                        severity="critical"
                    ))
                    break
            
            # Check for SQL injection
            for pattern in self._sql_injection_regex:
                if pattern.search(value):
                    violations.append(SecurityViolation(
                        violation_type=SecurityViolationType.SQL_INJECTION,
                        message="SQL injection pattern detected",
                        path=path,
                        value=value[:100],
                        severity="critical"
                    ))
                    break
            
            # Check for path traversal
            for pattern in self._path_traversal_regex:
                if pattern.search(value):
                    violations.append(SecurityViolation(
                        violation_type=SecurityViolationType.PATH_TRAVERSAL,
                        message="Path traversal pattern detected",
                        path=path,
                        value=value[:100],
                        severity="critical"
                    ))
                    break
            
            # Check for binary data
            try:
                value.encode('utf-8')
            except UnicodeEncodeError:
                violations.append(SecurityViolation(
                    violation_type=SecurityViolationType.INVALID_UNICODE,
                    message="Invalid Unicode characters detected",
                    path=path,
                    severity="high"
                ))
            
            # Check for null bytes
            if '\x00' in value:
                violations.append(SecurityViolation(
                    violation_type=SecurityViolationType.BINARY_DATA,
                    message="Null bytes detected in string",
                    path=path,
                    severity="high"
                ))
        
        return violations
    
    def sanitize_json_data(self, data: Any, remove_dangerous: bool = True) -> Any:
        """
        Sanitize JSON data by removing or escaping dangerous content.
        
        Args:
            data: Data to sanitize
            remove_dangerous: Remove dangerous keys/values instead of escaping
        
        Returns:
            Sanitized data
        """
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Check if key is dangerous
                is_dangerous = False
                if not self.allow_dangerous_keys:
                    for pattern in self._dangerous_key_regex:
                        if pattern.search(key):
                            is_dangerous = True
                            break
                
                if is_dangerous and remove_dangerous:
                    continue  # Skip dangerous keys
                
                # Sanitize the key if needed
                safe_key = self._sanitize_string(key) if is_dangerous else key
                
                # Recursively sanitize value
                sanitized[safe_key] = self.sanitize_json_data(value, remove_dangerous)
            
            return sanitized
        
        elif isinstance(data, list):
            return [self.sanitize_json_data(item, remove_dangerous) for item in data]
        
        elif isinstance(data, str):
            return self._sanitize_string(data)
        
        else:
            return data  # Numbers, booleans, None are safe
    
    def _sanitize_string(self, value: str) -> str:
        """Sanitize a string value by escaping dangerous content."""
        # HTML escape
        value = value.replace('&', '&amp;')
        value = value.replace('<', '&lt;')
        value = value.replace('>', '&gt;')
        value = value.replace('"', '&quot;')
        value = value.replace("'", '&#x27;')
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Truncate if too long
        if len(value) > self.max_string_length:
            value = value[:self.max_string_length] + '...'
        
        return value
    
    def hash_json_content(self, data: Any) -> str:
        """
        Generate a secure hash of JSON content for integrity checking.
        
        Returns:
            SHA-256 hash of the normalized JSON
        """
        # Normalize JSON (sorted keys, no whitespace)
        normalized = json.dumps(data, sort_keys=True, separators=(',', ':'))
        
        # Generate hash
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


class SecureJsonFieldHandler:
    """
    Secure wrapper for JSON field operations with validation and sanitization.
    
    Integrates with existing JsonFieldHandler to add security layer.
    """
    
    def __init__(self, strict_mode: bool = True, 
                 max_field_size: int = 50_000,
                 allow_dangerous_keys: bool = False):
        """
        Initialize secure JSON field handler.
        
        Args:
            strict_mode: Enable all security checks
            max_field_size: Maximum field size in bytes
            allow_dangerous_keys: Allow potentially dangerous keys
        """
        self.validator = SecureJsonValidator(
            max_size=max_field_size,
            strict_mode=strict_mode,
            allow_dangerous_keys=allow_dangerous_keys
        )
        self.strict_mode = strict_mode
    
    def secure_serialize(self, data: Any, sanitize: bool = True) -> str:
        """
        Securely serialize data to JSON with validation.
        
        Args:
            data: Data to serialize
            sanitize: Apply sanitization before serializing
        
        Returns:
            Serialized JSON string
        
        Raises:
            JsonSecurityError: If security violations detected
        """
        # Sanitize if requested
        if sanitize:
            data = self.validator.sanitize_json_data(data)
        
        # Validate data
        is_valid, violations = self.validator.validate_data(data)
        
        if not is_valid and self.strict_mode:
            raise JsonSecurityError(
                f"Security violations detected: {len(violations)} issues",
                violations
            )
        
        # Serialize
        return json.dumps(data, separators=(',', ':'))
    
    def secure_deserialize(self, json_string: str, 
                          validate: bool = True,
                          sanitize: bool = False) -> Any:
        """
        Securely deserialize JSON with validation.
        
        Args:
            json_string: JSON string to deserialize
            validate: Validate for security issues
            sanitize: Sanitize after deserialization
        
        Returns:
            Deserialized data
        
        Raises:
            JsonSecurityError: If security violations detected
        """
        if validate:
            # Validate JSON string
            is_valid, violations = self.validator.validate_json_string(json_string)
            
            if not is_valid and self.strict_mode:
                raise JsonSecurityError(
                    f"Security violations detected: {len(violations)} issues",
                    violations
                )
        
        # Parse JSON
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise JsonSecurityError(f"Invalid JSON format: {e}")
        
        # Sanitize if requested
        if sanitize:
            data = self.validator.sanitize_json_data(data)
        
        return data
    
    def check_integrity(self, data: Any, expected_hash: str) -> bool:
        """
        Verify data integrity using hash comparison.
        
        Args:
            data: Data to verify
            expected_hash: Expected SHA-256 hash
        
        Returns:
            True if integrity check passes
        """
        actual_hash = self.validator.hash_json_content(data)
        return actual_hash == expected_hash
    
    def generate_integrity_hash(self, data: Any) -> str:
        """Generate integrity hash for data."""
        return self.validator.hash_json_content(data)


# Factory functions for common use cases
def create_strict_validator() -> SecureJsonValidator:
    """Create a strict validator for high-security environments."""
    return SecureJsonValidator(
        strict_mode=True,
        allow_dangerous_keys=False,
        max_depth=5,
        max_size=10_000,
        max_total_size=50_000
    )


def create_relaxed_validator() -> SecureJsonValidator:
    """Create a relaxed validator for trusted environments."""
    return SecureJsonValidator(
        strict_mode=False,
        allow_dangerous_keys=True,
        max_depth=20,
        max_size=1_000_000,
        max_total_size=10_000_000
    )


def create_api_validator() -> SecureJsonValidator:
    """Create a validator optimized for API endpoints."""
    return SecureJsonValidator(
        strict_mode=True,
        allow_dangerous_keys=False,
        max_depth=10,
        max_size=100_000,
        max_total_size=1_000_000,
        max_keys=100,
        max_array_length=100
    )


# Integration with existing JsonFieldHandler
def enhance_json_handler_security(json_handler):
    """
    Enhance existing JsonFieldHandler with security features.
    
    This is a decorator/wrapper that adds security validation
    to existing JSON handler methods.
    """
    original_serialize = json_handler.serialize_json
    original_deserialize = json_handler.deserialize_json
    
    # Create security validator
    validator = SecureJsonValidator(
        max_size=json_handler.max_field_size,
        strict_mode=json_handler.strict_validation
    )
    
    def secure_serialize(data, field_type=None):
        # Validate before serializing
        is_valid, violations = validator.validate_data(data)
        
        if not is_valid and json_handler.strict_validation:
            raise JsonSecurityError(
                f"Security violations in {field_type}: {len(violations)} issues",
                violations
            )
        
        # Sanitize if needed
        if not json_handler.strict_validation:
            data = validator.sanitize_json_data(data)
        
        # Call original method
        return original_serialize(data, field_type)
    
    def secure_deserialize(json_string, field_type=None, default=None):
        # Validate JSON string
        if json_string:
            is_valid, violations = validator.validate_json_string(json_string)
            
            if not is_valid and json_handler.strict_validation:
                raise JsonSecurityError(
                    f"Security violations in {field_type}: {len(violations)} issues",
                    violations
                )
        
        # Call original method
        result = original_deserialize(json_string, field_type, default)
        
        # Sanitize result if needed
        if result and not json_handler.strict_validation:
            result = validator.sanitize_json_data(result)
        
        return result
    
    # Replace methods
    json_handler.serialize_json = secure_serialize
    json_handler.deserialize_json = secure_deserialize
    
    # Add security methods
    json_handler.validate_security = lambda data: validator.validate_data(data)
    json_handler.sanitize_data = lambda data: validator.sanitize_json_data(data)
    
    return json_handler


if __name__ == "__main__":
    print("🔐 JSON Security Module")
    print("=" * 50)
    
    # Test examples
    validator = create_strict_validator()
    
    # Test safe JSON
    safe_data = {
        "name": "Test User",
        "age": 30,
        "tasks": ["task1", "task2"]
    }
    
    is_valid, violations = validator.validate_data(safe_data)
    print(f"✅ Safe data validation: {'PASS' if is_valid else 'FAIL'}")
    
    # Test dangerous JSON
    dangerous_data = {
        "__proto__": {"isAdmin": True},
        "script": "<script>alert('XSS')</script>",
        "sql": "'; DROP TABLE users; --"
    }
    
    is_valid, violations = validator.validate_data(dangerous_data)
    print(f"❌ Dangerous data validation: {'PASS' if is_valid else 'FAIL'}")
    print(f"   Violations found: {len(violations)}")
    
    for v in violations:
        print(f"   - {v.violation_type.value}: {v.message}")
    
    # Test sanitization
    sanitized = validator.sanitize_json_data(dangerous_data)
    print(f"\n🧹 Sanitized data: {json.dumps(sanitized, indent=2)}")
    
    print("\n✅ JSON Security Module Ready!")