"""Security vulnerability checking module."""

import re
from typing import List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SecurityIssue:
    """Represents a security vulnerability."""
    severity: str  # 'low', 'medium', 'high', 'critical'
    category: str
    description: str
    line: int
    recommendation: str

class SecurityChecker:
    """Checker for security vulnerabilities."""
    
    def __init__(self):
        # Security patterns
        self.security_patterns = {
            'python': {
                r'eval\s*\(': 'Use of eval() - potential code injection vulnerability',
                r'exec\s*\(': 'Use of exec() - potential code injection vulnerability',
                r'subprocess\.call.*shell=True': 'Shell injection vulnerability',
                r'os\.system\s*\(': 'Command injection vulnerability',
                r'pickle\.loads?\s*\(': 'Unsafe deserialization - use json instead',
                r'yaml\.load\s*\(': 'Unsafe YAML loading - use safe_load',
                r'password\s*=\s*["\'][^"\']+["\']': 'Hardcoded password detected',
                r'secret\s*=\s*["\'][^"\']+["\']': 'Hardcoded secret detected',
                r'api_key\s*=\s*["\'][^"\']+["\']': 'Hardcoded API key detected',
                r'md5\s*\(': 'Weak hash algorithm MD5 detected',
                r'hashlib\.md5': 'Weak hash algorithm MD5 detected',
                r'random\.random\s*\(': 'Weak random number generator for crypto',
                r'urllib\.request\.urlopen.*verify=False': 'SSL verification disabled',
                r'ssl\..*CERT_NONE': 'SSL certificate verification disabled'
            },
            'javascript': {
                r'eval\s*\(': 'Use of eval() - potential code injection vulnerability',
                r'innerHTML\s*=': 'Potential XSS vulnerability - use textContent',
                r'document\.write\s*\(': 'Potential XSS vulnerability',
                r'\.html\s*\(.*\+': 'Potential XSS in jQuery html()',
                r'password.*=.*["\'][^"\']+["\']': 'Hardcoded password detected',
                r'Math\.random\s*\(': 'Weak random number generator for crypto',
                r'localStorage\.setItem.*password': 'Password stored in localStorage',
                r'sessionStorage\.setItem.*password': 'Password stored in sessionStorage'
            }
        }
    
    def find_security_issues(self, content: str, language: str) -> List[SecurityIssue]:
        """Find potential security vulnerabilities."""
        security_issues = []
        lines = content.split('\n')
        
        patterns = self.security_patterns.get(language, {})
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in patterns.items():
                if re.search(pattern, line):
                    severity = 'high'
                    if 'weak' in description.lower():
                        severity = 'medium'
                    elif 'hardcoded' in description.lower():
                        severity = 'critical'
                    
                    security_issues.append(SecurityIssue(
                        severity=severity,
                        category='code_security',
                        description=description,
                        line=line_num,
                        recommendation=self._get_security_recommendation(pattern)
                    ))
        
        return security_issues
    
    def _get_security_recommendation(self, pattern: str) -> str:
        """Get security recommendation for a pattern."""
        recommendations = {
            'eval': 'Avoid eval(). Use json.loads() for JSON or ast.literal_eval() for literals',
            'exec': 'Avoid exec(). Consider safer alternatives like importlib',
            'shell=True': 'Use shell=False and pass command as list',
            'os.system': 'Use subprocess.run() with proper argument handling',
            'pickle': 'Use json.dumps/loads or secure serialization libraries',
            'yaml.load': 'Use yaml.safe_load() instead of yaml.load()',
            'password.*=': 'Store passwords in environment variables or secure vaults',
            'secret.*=': 'Store secrets in environment variables or secure vaults',
            'api_key.*=': 'Store API keys in environment variables',
            'md5': 'Use SHA-256 or stronger hash algorithms',
            'random.random': 'Use secrets module for cryptographic purposes',
            'verify=False': 'Enable SSL verification for production code',
            'innerHTML': 'Use textContent or sanitize HTML input',
            'document.write': 'Use DOM manipulation methods instead',
            'localStorage.*password': 'Avoid storing sensitive data in browser storage'
        }
        
        for key, rec in recommendations.items():
            if key in pattern:
                return rec
        
        return 'Review and validate this security concern' 