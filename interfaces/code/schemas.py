from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class CodeIssue(BaseModel):
    type: str  # error, warning, info, security
    severity: str  # critical, high, medium, low
    message: str
    line: int
    column: int
    rule: str
    suggestion: Optional[str] = None

class CodeMetrics(BaseModel):
    lines_of_code: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    maintainability_index: float
    duplicated_lines: int
    test_coverage: float
    technical_debt_minutes: int

class SecurityIssue(BaseModel):
    severity: str
    category: str
    description: str
    line: int
    cwe_id: Optional[str] = None
    recommendation: Optional[str] = None

class AnalysisResult(BaseModel):
    file_path: str
    language: str
    metrics: CodeMetrics
    issues: List[CodeIssue]
    security_issues: List[SecurityIssue]
    suggestions: List[str]
    analysis_time: float

class FileAnalysisRequest(BaseModel):
    content: str
    filename: str
    language: Optional[str] = None

class ProjectAnalysisRequest(BaseModel):
    project_path: str
    include_patterns: Optional[List[str]] = Field(default_factory=lambda: ["*.py", "*.js", "*.ts"])
    exclude_patterns: Optional[List[str]] = Field(default_factory=lambda: ["node_modules/*", "*.min.js", "__pycache__/*"])

class ProjectSummary(BaseModel):
    total_files: int
    analyzed_files: int
    total_lines: int
    total_issues: int
    security_issues: int
    languages: Dict[str, int]
    issue_types: Dict[str, int]
    severity_distribution: Dict[str, int]

class ProjectAnalysisResult(BaseModel):
    summary: ProjectSummary
    files: Dict[str, AnalysisResult]
    recommendations: List[str]
    analysis_time: float

class CodeRefactorRequest(BaseModel):
    content: str
    language: str
    refactor_type: str = Field(..., description="Type of refactoring: extract_method, rename_variable, simplify_condition, etc.")
    target_line: Optional[int] = None
    new_name: Optional[str] = None

class RefactorSuggestion(BaseModel):
    type: str
    description: str
    original_code: str
    refactored_code: str
    confidence: float
    benefits: List[str]

class CodeRefactorResult(BaseModel):
    suggestions: List[RefactorSuggestion]
    applied_refactoring: Optional[str] = None
    success: bool
    message: str

class CodeReviewRequest(BaseModel):
    content: str
    filename: str
    reviewer_focus: Optional[str] = Field(default="general", description="Focus area: security, performance, maintainability, general")

class ReviewComment(BaseModel):
    line: int
    type: str  # suggestion, issue, compliment
    message: str
    severity: str
    category: str

class CodeReviewResult(BaseModel):
    overall_score: float  # 0-100
    comments: List[ReviewComment]
    summary: str
    strengths: List[str]
    areas_for_improvement: List[str]
    complexity_assessment: str

class DiffAnalysisRequest(BaseModel):
    original_content: str
    modified_content: str
    filename: str

class DiffChange(BaseModel):
    type: str  # added, removed, modified
    line_number: int
    content: str
    impact_score: float

class DiffAnalysisResult(BaseModel):
    changes: List[DiffChange]
    impact_summary: str
    quality_change: float  # -100 to 100, negative means quality decreased
    security_impact: str
    recommendations: List[str]

class CodeFormattingRequest(BaseModel):
    content: str
    language: str
    style_guide: Optional[str] = Field(default="pep8", description="Style guide to follow: pep8, google, black, prettier")

class FormattingResult(BaseModel):
    formatted_content: str
    changes_made: List[str]
    style_violations_fixed: int

class CodeComplexityRequest(BaseModel):
    content: str
    language: str
    
class ComplexityAnalysis(BaseModel):
    file_complexity: int
    function_complexities: Dict[str, int]
    most_complex_functions: List[Dict[str, Any]]
    complexity_distribution: Dict[str, int]
    recommendations: List[str]

class CodeDuplicationRequest(BaseModel):
    files: List[Dict[str, str]]  # filename -> content
    min_lines: Optional[int] = Field(default=5, description="Minimum lines for duplication detection")

class DuplicationBlock(BaseModel):
    files: List[str]
    start_lines: List[int]
    end_lines: List[int]
    similarity_score: float
    code_block: str

class DuplicationAnalysisResult(BaseModel):
    duplicated_blocks: List[DuplicationBlock]
    duplication_percentage: float
    total_duplicated_lines: int
    recommendations: List[str]

class CodeSearchRequest(BaseModel):
    query: str
    search_type: str = Field(..., description="Type: function, variable, class, pattern, security_issue")
    content: str
    language: str

class SearchMatch(BaseModel):
    line: int
    column: int
    match_text: str
    context: str
    confidence: float

class CodeSearchResult(BaseModel):
    matches: List[SearchMatch]
    total_matches: int
    search_time: float
    suggestions: List[str] 