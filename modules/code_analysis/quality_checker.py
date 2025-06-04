"""Code quality checking module."""

import ast
import re
from typing import List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CodeIssue:
    """Represents a code quality issue."""
    type: str  # 'quality', 'style', 'complexity', etc.
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    line: int
    column: int
    rule: str
    suggestion: str = ""

class QualityChecker:
    """Checker for code quality issues."""
    
    def __init__(self):
        # Code quality patterns
        self.quality_patterns = {
            'python': {
                r'except\s*:': 'Bare except clause - catch specific exceptions',
                r'print\s*\(': 'Print statement found - use logging instead',
                r'TODO': 'TODO comment found',
                r'FIXME': 'FIXME comment found',
                r'XXX': 'XXX comment found',
                r'def.*\([^)]{100,}\)': 'Long parameter list - consider refactoring',
                r'if.*and.*and.*and': 'Complex conditional - consider simplifying',
                r'lambda.*:.*lambda': 'Nested lambda functions - consider named functions'
            },
            'javascript': {
                r'console\.log': 'Console.log statement - remove before production',
                r'debugger': 'Debugger statement - remove before production',
                r'TODO': 'TODO comment found',
                r'FIXME': 'FIXME comment found',
                r'var\s+': 'Use of var - prefer let/const',
                r'==\s*[^=]': 'Use of == - prefer strict equality ===',
                r'!=\s*[^=]': 'Use of != - prefer strict inequality !=='
            }
        }
    
    def find_quality_issues(self, content: str, language: str) -> List[CodeIssue]:
        """Find code quality issues."""
        issues = []
        lines = content.split('\n')
        
        patterns = self.quality_patterns.get(language, {})
        
        for line_num, line in enumerate(lines, 1):
            for pattern, message in patterns.items():
                if re.search(pattern, line):
                    severity = 'medium'
                    if 'TODO' in pattern or 'FIXME' in pattern:
                        severity = 'low'
                    elif 'print' in pattern or 'console.log' in pattern:
                        severity = 'low'
                    
                    issues.append(CodeIssue(
                        type='quality',
                        severity=severity,
                        message=message,
                        line=line_num,
                        column=0,
                        rule=pattern
                    ))
        
        # Check for long lines
        for line_num, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(CodeIssue(
                    type='style',
                    severity='low',
                    message=f'Line too long ({len(line)} characters)',
                    line=line_num,
                    column=120,
                    rule='line_length'
                ))
        
        # Check for long functions/methods
        if language == 'python':
            self._check_python_function_length(content, issues)
        
        return issues
    
    def _check_python_function_length(self, content: str, issues: List[CodeIssue]):
        """Check Python function length."""
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno + 1
                    if func_lines > 50:
                        issues.append(CodeIssue(
                            type='complexity',
                            severity='medium',
                            message=f'Function "{node.name}" is too long ({func_lines} lines)',
                            line=node.lineno,
                            column=node.col_offset,
                            rule='function_length',
                            suggestion='Consider breaking this function into smaller functions'
                        ))
        except:
            pass 