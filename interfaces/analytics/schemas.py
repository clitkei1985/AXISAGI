from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

class SystemMetrics(BaseModel):
    timestamp: str
    users: Dict[str, Any]
    sessions: Dict[str, Any]
    messages: Dict[str, Any]
    memory: Dict[str, Any]
    plugins: Dict[str, Any]
    performance: Dict[str, Any]

class UserActivityAnalysis(BaseModel):
    total_sessions: int
    total_messages: int
    total_memories: int
    most_active_day: Optional[str]
    avg_daily_sessions: float

class UsagePatterns(BaseModel):
    peak_hour: Optional[int]
    peak_day: Optional[str]
    hour_distribution: Dict[str, int]
    day_distribution: Dict[str, int]

class MemoryUsageAnalysis(BaseModel):
    total_memories: int
    source_distribution: Dict[str, int]
    most_common_tags: Dict[str, int]

class UserAnalytics(BaseModel):
    user_id: int
    username: str
    period_days: int
    activity: UserActivityAnalysis
    usage_patterns: UsagePatterns
    memory_usage: MemoryUsageAnalysis
    engagement_score: float

class SessionInfo(BaseModel):
    created_at: str
    updated_at: Optional[str]
    duration: float
    session_type: str

class MessageStats(BaseModel):
    total_messages: int
    user_messages: int
    assistant_messages: int
    avg_user_message_length: float
    avg_assistant_message_length: float
    message_frequency: float

class ConversationFlow(BaseModel):
    total_turns: int
    avg_turn_length: float
    role_distribution: Dict[str, int]

class SentimentAnalysis(BaseModel):
    overall_sentiment: str
    sentiment_trend: str
    positive_ratio: float
    negative_ratio: float
    neutral_ratio: float

class ChatAnalytics(BaseModel):
    session_id: int
    session_info: SessionInfo
    message_stats: MessageStats
    conversation_flow: ConversationFlow
    topics: List[str]
    sentiment: SentimentAnalysis

class ReportRequest(BaseModel):
    report_type: str = Field(..., description="Type of report: system_overview, user_engagement, performance, content_analysis")
    start_date: datetime
    end_date: datetime
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)

class TimelinePeriod(BaseModel):
    date: str
    sessions: int
    messages: int

class SystemTrends(BaseModel):
    timeline: List[TimelinePeriod]
    growth_rate: float

class SystemOverviewReport(BaseModel):
    report_type: str
    period: Dict[str, str]
    summary: SystemMetrics
    trends: SystemTrends
    generated_at: str

class UserEngagementSummary(BaseModel):
    total_active_users: int
    avg_engagement_score: float

class UserEngagementReport(BaseModel):
    report_type: str
    period: Dict[str, str]
    summary: UserEngagementSummary
    user_data: List[UserAnalytics]
    generated_at: str

class PerformanceReport(BaseModel):
    report_type: str
    period: Dict[str, str]
    metrics: Dict[str, Any]
    generated_at: str

class ContentStats(BaseModel):
    total_messages: int
    avg_length: float
    topics: List[str]
    sentiment: SentimentAnalysis

class ContentAnalysisReport(BaseModel):
    report_type: str
    period: Dict[str, str]
    content_stats: ContentStats
    generated_at: str

class AnalyticsReport(BaseModel):
    """Union type for all report types."""
    report_type: str
    period: Dict[str, str]
    generated_at: str
    data: Union[SystemOverviewReport, UserEngagementReport, PerformanceReport, ContentAnalysisReport]

class MetricsFilter(BaseModel):
    user_ids: Optional[List[int]] = None
    session_types: Optional[List[str]] = None
    include_archived: bool = False
    min_engagement_score: Optional[float] = None

class DashboardWidget(BaseModel):
    widget_id: str
    title: str
    type: str  # chart, metric, table, etc.
    data: Dict[str, Any]
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class Dashboard(BaseModel):
    dashboard_id: str
    name: str
    description: Optional[str]
    widgets: List[DashboardWidget]
    layout: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AlertRule(BaseModel):
    rule_id: str
    name: str
    description: Optional[str]
    metric: str  # The metric to monitor
    condition: str  # >, <, ==, etc.
    threshold: float
    enabled: bool = True
    notification_channels: List[str] = Field(default_factory=list)

class Alert(BaseModel):
    alert_id: str
    rule_id: str
    triggered_at: datetime
    resolved_at: Optional[datetime]
    severity: str  # low, medium, high, critical
    message: str
    current_value: float
    threshold_value: float
    status: str = "active"  # active, acknowledged, resolved

class ExportRequest(BaseModel):
    export_type: str = Field(..., description="Type of export: csv, json, pdf")
    data_type: str = Field(..., description="Type of data: metrics, report, raw_data")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ExportResponse(BaseModel):
    export_id: str
    status: str = "processing"  # processing, completed, failed
    download_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    file_size: Optional[int] = None 