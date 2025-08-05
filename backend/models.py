"""
Pydantic models for BorgDash API
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Archive(BaseModel):
    """Backup archive model"""
    name: str = Field(..., description="Archive name")
    createdAt: datetime = Field(..., description="Archive creation timestamp")
    originalSize: str = Field(..., description="Original data size")
    compressedSize: str = Field(..., description="Compressed size")
    deduplicatedSize: str = Field(..., description="Deduplicated size")


class BackupRun(BaseModel):
    """Backup run model"""
    id: str = Field(..., description="Unique run identifier")
    status: str = Field(..., description="Run status (success, warning, error)")
    timestamp: datetime = Field(..., description="Run start timestamp")
    timestampRelative: Optional[str] = Field(None, description="Run timestamp relative time (e.g., '2 hours ago')")
    duration: Optional[str] = Field(None, description="Run duration")
    endTimestamp: Optional[datetime] = Field(None, description="Run end timestamp")


class JobStats(BaseModel):
    """Job statistics model"""
    archiveCount: int = Field(0, description="Total number of archives")
    fullSize: str = Field("0 B", description="Total original data size")
    compressedSize: str = Field("0 B", description="Total compressed size")
    deduplicatedSize: str = Field("0 B", description="Total deduplicated size")
    compressionRatio: str = Field("0%", description="Compression efficiency")


class JobSummary(BaseModel):
    """Job summary for dashboard list"""
    jobId: str = Field(..., description="Unique job identifier")
    name: str = Field(..., description="Job display name")
    status: str = Field(..., description="Current job status")
    scheduleStatus: str = Field(..., description="Schedule compliance status")
    lastBackup: Optional[datetime] = Field(None, description="Last backup timestamp")
    lastBackupRelative: Optional[str] = Field(None, description="Last backup relative time (e.g., '2 days ago')")
    lastSuccessfulBackup: Optional[datetime] = Field(None, description="Last successful backup timestamp")
    lastSuccessfulBackupRelative: Optional[str] = Field(None, description="Last successful backup relative time")
    tags: List[str] = Field(default_factory=list, description="Job tags")
    stats: JobStats = Field(default_factory=JobStats, description="Job statistics")


class BackupEvent(BaseModel):
    """Backup event model"""
    id: str = Field(..., description="Unique event identifier")
    type: str = Field(..., description="Event type (start, stop, success, failed, log, info)")
    timestamp: datetime = Field(..., description="Event timestamp")
    timestampRelative: Optional[str] = Field(None, description="Event timestamp relative time")
    message: str = Field(..., description="Event message/summary")
    hasInfo: bool = Field(False, description="Whether this event has expandable info")
    extra: Optional[Dict[str, Any]] = Field(None, description="Additional event data")


class PushEventRequest(BaseModel):
    """Request model for pushing events"""
    job_id: str = Field(..., description="Job identifier")
    type: str = Field(..., description="Event type")
    message: str = Field(..., description="Event message/summary")
    info: Optional[str] = Field(None, description="Optional detailed info/log content")
    extra: Optional[Dict[str, Any]] = Field(None, description="Additional event data")


class Job(JobSummary):
    """Detailed job model"""
    description: Optional[str] = Field(None, description="Job description")
    backupType: str = Field("borgmatic", description="Backup type (borg/borgmatic)")
    maxAge: str = Field("24h", description="Maximum age before considered overdue")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")
