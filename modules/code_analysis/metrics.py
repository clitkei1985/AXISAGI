"""Code metrics calculation module."""

import ast
import re
import time
from dataclasses import dataclass
from collections import Counter
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class CodeMetrics:
    """Code complexity and quality metrics."""
    lines_of_code: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    maintainability_index: float
    duplicated_lines: int
    test_coverage: float
    technical_debt_minutes: int

class MetricsCalculator:
    """Calculator for various code metrics."""
    
    def calculate_metrics(self, content: str, language: str) -> CodeMetrics:
        """Calculate various code metrics."""
        lines = content.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        # Basic complexity metrics
        cyclomatic = self._calculate_cyclomatic_complexity(content, language)
        cognitive = self._calculate_cognitive_complexity(content, language)
        maintainability = self._calculate_maintainability_index(content, language)
        duplicated = self._find_duplicated_lines(content)
        
        return CodeMetrics(
            lines_of_code=loc,
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            maintainability_index=maintainability,
            duplicated_lines=duplicated,
            test_coverage=0.0,  # Would need external tool integration
            technical_debt_minutes=max(0, (100 - maintainability) * 5)
        )
    
    def _calculate_cyclomatic_complexity(self, content: str, language: str) -> int:
        """Calculate cyclomatic complexity."""
        if language == 'python':
            try:
                tree = ast.parse(content)
                complexity = 1  # Base complexity
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.If, ast.While, ast.For, ast.Try,
                                       ast.With, ast.AsyncWith, ast.ListComp,
                                       ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                        complexity += 1
                    elif isinstance(node, ast.BoolOp):
                        complexity += len(node.values) - 1
                    elif isinstance(node, ast.ExceptHandler):
                        complexity += 1
                
                return complexity
            except:
                pass
        
        # Fallback for other languages or parsing errors
        complexity_keywords = {
            'python': ['if', 'elif', 'while', 'for', 'try', 'except', 'and', 'or'],
            'javascript': ['if', 'else', 'while', 'for', 'switch', 'case', 'catch', '&&', '||', '?'],
            'java': ['if', 'else', 'while', 'for', 'switch', 'case', 'catch', '&&', '||', '?'],
        }
        
        keywords = complexity_keywords.get(language, ['if', 'while', 'for'])
        count = 1  # Base complexity
        
        for keyword in keywords:
            count += len(re.findall(r'\b' + keyword + r'\b', content))
        
        return count
    
    def _calculate_cognitive_complexity(self, content: str, language: str) -> int:
        """Calculate cognitive complexity (how hard code is to understand)."""
        # Simplified cognitive complexity calculation
        cognitive = 0
        nesting_level = 0
        
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()
            
            # Increase nesting for control structures
            if any(keyword in stripped for keyword in ['if', 'for', 'while', 'try', 'with']):
                cognitive += (1 + nesting_level)
                if stripped.endswith(':'):
                    nesting_level += 1
            
            # Logical operators add to complexity
            cognitive += len(re.findall(r'\b(and|or)\b', stripped))
            cognitive += len(re.findall(r'(&&|\|\|)', stripped))
            
            # Decrease nesting (simplified)
            if stripped.startswith(('except', 'finally', 'else')):
                nesting_level = max(0, nesting_level - 1)
        
        return cognitive
    
    def _calculate_maintainability_index(self, content: str, language: str) -> float:
        """Calculate maintainability index (0-100, higher is better)."""
        loc = len(content.split('\n'))
        cyclomatic = self._calculate_cyclomatic_complexity(content, language)
        halstead_volume = self._calculate_halstead_volume(content, language)
        
        # Simplified maintainability index calculation
        mi = max(0, (171 - 5.2 * halstead_volume - 0.23 * cyclomatic - 16.2 * loc) * 100 / 171)
        return round(mi, 2)
    
    def _calculate_halstead_volume(self, content: str, language: str) -> float:
        """Calculate Halstead volume (simplified)."""
        # Count unique operators and operands
        operators = set()
        operands = set()
        
        # Basic patterns for different languages
        operator_patterns = {
            'python': r'[+\-*/%=<>!&|^~]|and|or|not|in|is',
            'javascript': r'[+\-*/%=<>!&|^~?:]|&&|\|\||===|!==',
        }
        
        pattern = operator_patterns.get(language, r'[+\-*/%=<>!&|^~]')
        operators.update(re.findall(pattern, content))
        
        # Count words as operands (simplified)
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
        operands.update(words)
        
        n1, n2 = len(operators), len(operands)
        N1 = sum(content.count(op) for op in operators)
        N2 = sum(content.count(op) for op in operands)
        
        if n1 == 0 or n2 == 0:
            return 0.0
        
        vocabulary = n1 + n2
        length = N1 + N2
        volume = length * (vocabulary.bit_length() if vocabulary > 0 else 0)
        
        return volume / 1000.0  # Scale down
    
    def _find_duplicated_lines(self, content: str) -> int:
        """Find duplicated lines of code."""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        line_counts = Counter(lines)
        duplicated = sum(count - 1 for count in line_counts.values() if count > 1)
        return duplicated 