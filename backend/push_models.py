#!/usr/bin/env python3
"""
Push API Models for BorgDash
Data models for receiving backup information from Borg/Borgmatic hooks
"""

from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel
from datetime import datetime


class PushStatusRequest(BaseModel):
    """Status/log information for a backup run"""
    job_id: str
    run_id: str
    status: Literal["success", "failed", "running", "warning"]
    start_time: datetime
    end_time: Optional[datetime] = None
    exit_code: Optional[int] = None
    log_lines: List[str] = []
    error_message: Optional[str] = None


class BorgInfoRequest(BaseModel):
    """Borg repository info and archive list"""
    job_id: str
    repository_info: Dict[str, Any]  # Output of 'borg info'
    archive_list: List[Dict[str, Any]]  # Output of 'borg list --json'


class BorgmaticInfoRequest(BaseModel):
    """Borgmatic repository info"""
    job_id: str
    info_data: Union[List[Dict[str, Any]], Dict[str, Any]]  # Output of 'borgmatic info --json' (array or single dict)
    repository_label: Optional[str] = None  # Filter for specific repo in multi-repo setups


class BorgmaticRinfoRequest(BaseModel):
    """Borgmatic repository and archive info"""
    job_id: str
    rinfo_data: Union[List[Dict[str, Any]], Dict[str, Any]]  # Output of 'borgmatic rinfo --json' (array or single dict)
    repository_label: Optional[str] = None  # Filter for specific repo in multi-repo setups


class PushResponse(BaseModel):
    """Standard response for push endpoints"""
    success: bool
    message: str
    job_id: str
    timestamp: datetime
