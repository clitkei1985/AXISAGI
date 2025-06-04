from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

# System Management Schemas

class SystemStatus(BaseModel):
    status: str  # healthy, warning, critical
    uptime_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    disk_usage_percent: float
    active_users: int
    active_sessions: int
    database_status: str
    last_backup: Optional[datetime]
    version: str

class SystemConfig(BaseModel):
    debug_mode: bool
    log_level: str
    max_users: int
    session_timeout_hours: int
    backup_enabled: bool
    backup_interval_hours: int
    maintenance_mode: bool
    features_enabled: Dict[str, bool]

class SystemConfigUpdate(BaseModel):
    debug_mode: Optional[bool] = None
    log_level: Optional[str] = None
    max_users: Optional[int] = None
    session_timeout_hours: Optional[int] = None
    backup_enabled: Optional[bool] = None
    backup_interval_hours: Optional[int] = None
    maintenance_mode: Optional[bool] = None
    features_enabled: Optional[Dict[str, bool]] = None

# User Management Schemas

class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]
    session_count: int
    total_messages: int
    storage_used_mb: float

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=8)
    is_admin: bool = False

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class BulkUserAction(BaseModel):
    user_ids: List[int]
    action: str  # activate, deactivate, delete, reset_password
    reason: Optional[str] = None

# Database Management Schemas

class DatabaseStats(BaseModel):
    total_users: int
    total_sessions: int
    total_messages: int
    total_memories: int
    total_plugins: int
    database_size_mb: float
    table_sizes: Dict[str, float]
    connection_count: int
    slowest_queries: List[Dict[str, Any]]

class BackupInfo(BaseModel):
    backup_id: str
    created_at: datetime
    size_mb: float
    type: str  # full, incremental
    status: str  # completed, in_progress, failed
    file_path: str

class BackupRequest(BaseModel):
    type: str = Field(default="full", description="Type: full, incremental")
    include_uploads: bool = True
    compression: bool = True

class RestoreRequest(BaseModel):
    backup_id: str
    restore_uploads: bool = True
    confirm: bool = Field(..., description="Must be true to confirm restore")

# Plugin Management Schemas

class PluginInfo(BaseModel):
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    enabled: bool
    installed_at: datetime
    last_updated: Optional[datetime]
    dependencies: List[str]
    permissions: List[str]
    file_size_mb: float

class PluginInstallRequest(BaseModel):
    plugin_file: str  # Path or URL to plugin
    enable_immediately: bool = False
    overwrite_existing: bool = False

class PluginConfigUpdate(BaseModel):
    plugin_id: str
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None

# Log Management Schemas

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    logger: str
    message: str
    user_id: Optional[int]
    session_id: Optional[str]
    ip_address: Optional[str]
    extra_data: Optional[Dict[str, Any]]

class LogQuery(BaseModel):
    level: Optional[str] = None
    logger: Optional[str] = None
    user_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    search_text: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

class LogStats(BaseModel):
    total_entries: int
    entries_by_level: Dict[str, int]
    entries_by_logger: Dict[str, int]
    error_rate_24h: float
    warning_rate_24h: float

# Monitoring and Alerts Schemas

class AlertRule(BaseModel):
    rule_id: str
    name: str
    description: str
    condition: str  # metric > threshold, error_rate > 0.1, etc.
    threshold: float
    enabled: bool
    notification_channels: List[str]
    cooldown_minutes: int

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

class MetricValue(BaseModel):
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Optional[Dict[str, str]] = None

class SystemHealth(BaseModel):
    overall_status: str  # healthy, degraded, critical
    components: Dict[str, str]  # component -> status
    active_alerts: List[Alert]
    performance_metrics: List[MetricValue]
    uptime_percentage: float

# Maintenance Schemas

class MaintenanceWindow(BaseModel):
    window_id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    affected_services: List[str]
    status: str  # scheduled, in_progress, completed, cancelled
    created_by: str

class MaintenanceTask(BaseModel):
    task_id: str
    window_id: str
    name: str
    description: str
    estimated_duration_minutes: int
    status: str  # pending, in_progress, completed, failed
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    logs: List[str]

# Security Management Schemas

class SecurityEvent(BaseModel):
    event_id: str
    timestamp: datetime
    event_type: str  # login_failed, suspicious_activity, etc.
    severity: str
    user_id: Optional[int]
    ip_address: str
    user_agent: Optional[str]
    details: Dict[str, Any]
    status: str = "open"  # open, investigating, resolved

class SecurityRule(BaseModel):
    rule_id: str
    name: str
    description: str
    rule_type: str  # rate_limiting, ip_blocking, etc.
    conditions: Dict[str, Any]
    actions: List[str]
    enabled: bool

class SecurityAudit(BaseModel):
    audit_id: str
    performed_at: datetime
    performed_by: str
    audit_type: str  # security_scan, penetration_test, etc.
    findings: List[Dict[str, Any]]
    risk_level: str
    recommendations: List[str]

# Audit Trail Schemas

class AuditLogEntry(BaseModel):
    id: int
    timestamp: datetime
    user_id: int
    username: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Dict[str, Any]
    ip_address: str
    user_agent: Optional[str]

class AuditQuery(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=50, le=500)
    offset: int = Field(default=0, ge=0)

# Performance Monitoring Schemas

class PerformanceMetrics(BaseModel):
    response_times: Dict[str, float]  # endpoint -> avg_response_time
    throughput: Dict[str, float]  # endpoint -> requests_per_second
    error_rates: Dict[str, float]  # endpoint -> error_rate
    resource_usage: Dict[str, float]  # cpu, memory, disk
    database_metrics: Dict[str, float]
    cache_metrics: Dict[str, float]

class PerformanceReport(BaseModel):
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    summary: PerformanceMetrics
    recommendations: List[str]
    alerts_triggered: int
    sla_breaches: List[Dict[str, Any]]

# API Management Schemas

class APIEndpoint(BaseModel):
    path: str
    method: str
    calls_24h: int
    avg_response_time_ms: float
    error_rate_percent: float
    last_error: Optional[datetime]
    rate_limit: Optional[int]
    authentication_required: bool

class APIKey(BaseModel):
    key_id: str
    name: str
    created_at: datetime
    last_used: Optional[datetime]
    usage_count: int
    rate_limit: Optional[int]
    permissions: List[str]
    expires_at: Optional[datetime]
    is_active: bool

class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str]
    rate_limit: Optional[int] = None
    expires_at: Optional[datetime] = None

# Response Schemas

class AdminActionResult(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    affected_count: Optional[int] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    checks: Dict[str, Dict[str, Any]]
    version: str 