"""Main code analyzer module."""

import time
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
import logging

from .metrics import CodeMetrics, MetricsCalculator
from .quality_checker import CodeIssue, QualityChecker
from .security_checker import SecurityIssue, SecurityChecker
from .suggestion_generator import SuggestionGenerator

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Complete analysis result for a file."""
    file_path: str
    language: str
    metrics: CodeMetrics
    issues: List[CodeIssue]
    security_issues: List[SecurityIssue]
    suggestions: List[str]
    analysis_time: float

class CodeAnalyzer:
    """Advanced code analyzer with multiple analysis capabilities."""
    
    def __init__(self):
        self.supported_languages = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php'
        }
        
        # Initialize components
        self.metrics_calculator = MetricsCalculator()
        self.quality_checker = QualityChecker()
        self.security_checker = SecurityChecker()
        self.suggestion_generator = SuggestionGenerator()
        
        # Initialize project analyzer lazily to avoid circular import
        self.project_analyzer = None
    
    def _get_project_analyzer(self):
        """Get project analyzer instance, creating it if needed."""
        if self.project_analyzer is None:
            from .project_analyzer import ProjectAnalyzer
            self.project_analyzer = ProjectAnalyzer(self)
        return self.project_analyzer
    
    async def analyze_file(self, file_path: str, content: str = None) -> AnalysisResult:
        """Analyze a single file and return comprehensive results."""
        start_time = time.time()
        
        # Determine language
        file_ext = Path(file_path).suffix.lower()
        language = self.supported_languages.get(file_ext, 'unknown')
        
        if content is None:
            content = self._read_file_content(file_path)
            if content is None:
                return self._create_error_result(file_path, language, start_time)
        
        # Perform various analyses
        metrics = self.metrics_calculator.calculate_metrics(content, language)
        issues = self.quality_checker.find_quality_issues(content, language)
        security_issues = self.security_checker.find_security_issues(content, language)
        suggestions = self.suggestion_generator.generate_suggestions(content, language, issues, security_issues)
        
        return AnalysisResult(
            file_path=file_path,
            language=language,
            metrics=metrics,
            issues=issues,
            security_issues=security_issues,
            suggestions=suggestions,
            analysis_time=time.time() - start_time
        )
    
    async def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze an entire project directory."""
        return await self._get_project_analyzer().analyze_project(project_path)
    
    def _read_file_content(self, file_path: str) -> str:
        """Read file content safely."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def _create_error_result(self, file_path: str, language: str, start_time: float) -> AnalysisResult:
        """Create an error result for failed file reads."""
        return AnalysisResult(
            file_path=file_path,
            language=language,
            metrics=CodeMetrics(0, 0, 0, 0.0, 0, 0.0, 0),
            issues=[],
            security_issues=[],
            suggestions=[],
            analysis_time=time.time() - start_time
        )

# Singleton instance
_code_analyzer = None

def get_code_analyzer() -> CodeAnalyzer:
    """Get or create the CodeAnalyzer instance."""
    global _code_analyzer
    if _code_analyzer is None:
        _code_analyzer = CodeAnalyzer()
    return _code_analyzer
