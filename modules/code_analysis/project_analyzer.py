import time
import logging
from pathlib import Path
from collections import Counter
from typing import Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .analyzer import AnalysisResult, CodeAnalyzer

logger = logging.getLogger(__name__)

class ProjectAnalyzer:
    """Handles project-level code analysis operations."""
    
    def __init__(self, code_analyzer: "CodeAnalyzer"):
        self.code_analyzer = code_analyzer
    
    async def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze an entire project directory."""
        start_time = time.time()
        project_path = Path(project_path)
        
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        results = {}
        summary = self._create_empty_summary()
        
        # Find all code files
        code_files = self._find_code_files(project_path)
        summary['total_files'] = len(code_files)
        
        # Analyze each file
        for file_path in code_files:
            try:
                result = await self.code_analyzer.analyze_file(str(file_path))
                results[str(file_path.relative_to(project_path))] = result
                self._update_summary(summary, result)
                    
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
        
        return {
            'summary': summary,
            'files': results,
            'recommendations': self._generate_project_recommendations(summary, results),
            'analysis_time': time.time() - start_time
        }
    
    def _create_empty_summary(self) -> Dict[str, Any]:
        """Create an empty summary structure."""
        return {
            'total_files': 0,
            'analyzed_files': 0,
            'total_lines': 0,
            'total_issues': 0,
            'security_issues': 0,
            'languages': Counter(),
            'issue_types': Counter(),
            'severity_distribution': Counter()
        }
    
    def _find_code_files(self, project_path: Path) -> List[Path]:
        """Find all code files in the project directory."""
        code_files = []
        for ext in self.code_analyzer.supported_languages.keys():
            code_files.extend(project_path.rglob(f"*{ext}"))
        return code_files
    
    def _update_summary(self, summary: Dict[str, Any], result: "AnalysisResult"):
        """Update the summary with results from a single file analysis."""
        summary['analyzed_files'] += 1
        summary['total_lines'] += result.metrics.lines_of_code
        summary['total_issues'] += len(result.issues)
        summary['security_issues'] += len(result.security_issues)
        summary['languages'][result.language] += 1
        
        for issue in result.issues:
            summary['issue_types'][issue.type] += 1
            summary['severity_distribution'][issue.severity] += 1
        
        for sec_issue in result.security_issues:
            summary['severity_distribution'][sec_issue.severity] += 1
    
    def _generate_project_recommendations(self, summary: Dict, results: Dict) -> List[str]:
        """Generate project-level recommendations."""
        recommendations = []
        
        # Overall quality assessment
        if summary['total_issues'] > summary['total_lines'] * 0.1:
            recommendations.append("High issue density - consider establishing coding standards")
        
        if summary['security_issues'] > 0:
            recommendations.append("Security issues detected - implement security review process")
        
        # Language distribution
        if len(summary['languages']) > 5:
            recommendations.append("Multiple languages detected - ensure consistent standards across all")
        
        # File size recommendations
        large_files = [path for path, result in results.items() 
                      if result.metrics.lines_of_code > 500]
        if len(large_files) > 3:
            recommendations.append(f"Consider refactoring large files: {', '.join(large_files[:3])}")
        
        return recommendations 