from collections import Counter
from typing import List

from .quality_checker import CodeIssue
from .security_checker import SecurityIssue

class SuggestionGenerator:
    """Generates improvement suggestions based on code analysis results."""
    
    def generate_suggestions(self, content: str, language: str, issues: List[CodeIssue], 
                           security_issues: List[SecurityIssue]) -> List[str]:
        """Generate improvement suggestions based on analysis."""
        suggestions = []
        
        # Based on metrics
        lines = len(content.split('\n'))
        if lines > 500:
            suggestions.append("Consider breaking this file into smaller modules")
        
        # Based on issues
        issue_counts = Counter(issue.type for issue in issues)
        if issue_counts.get('complexity', 0) > 5:
            suggestions.append("Multiple complexity issues detected - consider refactoring")
        
        if issue_counts.get('style', 0) > 10:
            suggestions.append("Many style issues detected - consider using a code formatter")
        
        # Based on security issues
        if len(security_issues) > 0:
            suggestions.append("Security vulnerabilities detected - review and fix immediately")
        
        # Language-specific suggestions
        if language == 'python':
            if any('print(' in content for line in content.split('\n')):
                suggestions.append("Consider using logging instead of print statements")
        
        return suggestions 