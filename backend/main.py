
#!/usr/bin/env python3
# BorgDash Backend Server
# A FastAPI-based backup monitoring dashboard for Borg/Borgmatic systems.

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import toml
from models import Job, Archive, BackupRun, JobSummary, BackupEvent, PushEventRequest
from config import Config, load_config
from storage import DataStorage
from auth import AuthManager, LoginRequest, LoginResponse
from push_models import (
    PushStatusRequest, BorgInfoRequest, BorgmaticInfoRequest, 
    BorgmaticRinfoRequest, PushResponse
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
config: Config
storage: DataStorage
auth_manager: AuthManager


async def get_api_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> str:
    """Dependency to get API token for job validation"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not auth_manager.verify_api_token(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> str:
    """Dependency to get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = auth_manager.verify_token(credentials.credentials)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return username


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global config, storage, auth_manager
    
    # Startup
    logger.info("Starting BorgDash Backend...")
    
    # Config path detection with debugging
    config_path = os.environ.get("BORGDASH_CONFIG", "/config/config.toml")
    logger.info(f"Config path: {config_path}")
    logger.info(f"Config path exists: {Path(config_path).exists()}")
    logger.info(f"Config path absolute: {Path(config_path).absolute()}")
    
    config = load_config(config_path)
    storage = DataStorage(config)
    auth_manager = AuthManager(config)
    
    # Ensure data directories exist
    storage.ensure_directories()
    
    # Debug config directory contents
    config_dir_path = Path(config.server.config_dir)
    logger.info(f"Config directory: {config_dir_path.absolute()}")
    logger.info(f"Config directory exists: {config_dir_path.exists()}")
    
    if config_dir_path.exists():
        try:
            config_files = list(config_dir_path.glob("*.toml"))
            logger.info(f"Config files found: {[str(f) for f in config_files]}")
            
            # List all files in config directory for debugging
            all_files = list(config_dir_path.iterdir())
            logger.info(f"All files in config directory: {[str(f) for f in all_files]}")
        except Exception as e:
            logger.warning(f"Could not list config directory contents: {e}")
    else:
        logger.warning(f"Config directory does not exist: {config_dir_path}")
    
    logger.info(f"Server configured on port {config.server.port}")
    logger.info(f"Data directory: {config.server.data_dir}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BorgDash Backend...")


app = FastAPI(
    title="BorgDash API",
    description="Backup monitoring dashboard for Borg/Borgmatic systems",
    version="1.0.0",
    lifespan=lifespan
)


# Serve static frontend (Vue build output) under /ui
frontend_dist = Path(__file__).parent / "static"
if frontend_dist.exists():
    app.mount("/ui", StaticFiles(directory=str(frontend_dist), html=True), name="ui-static")
else:
    # Fallback for development - look for dist in parent directory
    frontend_dist_dev = Path(__file__).parent.parent / "frontend" / "dist"
    if frontend_dist_dev.exists():
        app.mount("/ui", StaticFiles(directory=str(frontend_dist_dev), html=True), name="ui-static")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication endpoints
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    if not auth_manager.verify_credentials(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token, expires_at = auth_manager.create_access_token(request.username)
    return LoginResponse(
        access_token=token,
        expires_at=expires_at
    )


@app.post("/auth/verify")
async def verify_token(current_user: str = Depends(get_current_user)):
    """Verify the current token is valid and return user info"""
    return {"valid": True, "user": current_user}


# API Routes

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/jobs", response_model=List[JobSummary])
async def get_jobs(current_user: str = Depends(get_current_user)):
    """Get all backup jobs with summary information"""
    try:
        jobs = storage.get_all_jobs()
        return jobs
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str, current_user: str = Depends(get_current_user)):
    """Get detailed information for a specific job"""
    try:
        job = storage.get_job_details(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/jobs/{job_id}/archives", response_model=Dict[str, Any])
async def get_job_archives(
    job_id: str,
    current_user: str = Depends(get_current_user),
    offset: int = Query(0, ge=0),
    limit: int = Query(15, ge=1, le=100),
    sort_by: str = Query("date", regex="^(date|name|originalSize|compressedSize|deduplicatedSize)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    """Get archives for a specific job with pagination and sorting"""
    try:
        result = storage.get_job_archives(job_id, offset, limit, sort_by, sort_order)
        if not result:
            raise HTTPException(status_code=404, detail="Job not found")
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    except Exception as e:
        logger.error(f"Error getting archives for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/jobs/{job_id}/runs", response_model=List[BackupRun])
async def get_job_runs(
    job_id: str,
    current_user: str = Depends(get_current_user),
    limit: int = Query(15, ge=1, le=50)
):
    """Get recent backup runs for a specific job"""
    try:
        runs = storage.get_job_runs(job_id, limit)
        if runs is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return runs
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    except Exception as e:
        logger.error(f"Error getting runs for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/jobs/{job_id}/runs/{run_id}", response_model=Dict[str, Any])
async def get_job_run_details(
    job_id: str,
    run_id: str,
    current_user: str = Depends(get_current_user),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    """Get detailed information for a specific backup run including logs"""
    try:
        result = storage.get_run_details(job_id, run_id, offset, limit)
        if not result:
            raise HTTPException(status_code=404, detail="Run not found")
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        logger.error(f"Error getting run details {job_id}/{run_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Event API Endpoints
@app.get("/api/jobs/{job_id}/events", response_model=Dict[str, Any])
async def get_job_events(
    job_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(15, ge=1, le=100),
    current_user: str = Depends(get_current_user)
):
    """Get events for a specific job with pagination (sorted by timestamp desc)"""
    try:
        result = storage.get_job_events(job_id, offset, limit)
        if result is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return result
    except Exception as e:
        logger.error(f"Error getting events for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/jobs/{job_id}/events/{event_id}/info", response_model=Dict[str, Any])
async def get_event_info(
    job_id: str,
    event_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: str = Depends(get_current_user)
):
    """Get info content for a specific event with pagination"""
    try:
        result = storage.get_event_info(job_id, event_id, offset, limit)
        if result is None:
            raise HTTPException(status_code=404, detail="Event info not found")
        return result
    except Exception as e:
        logger.error(f"Error getting event info for {job_id}/{event_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/jobs/{job_id}/sync", response_model=Dict[str, Any])
async def sync_job_summary(
    job_id: str,
    current_user: str = Depends(get_current_user)
):
    """Sync job summary by processing all events chronologically"""
    try:
        # Verify job exists in configuration
        job_configs = storage.get_all_job_configs()
        if job_id not in job_configs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        result = storage.sync_job_summary_from_events(job_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing job summary for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/push/event", response_model=PushResponse)
async def push_event(request: PushEventRequest, api_token: str = Depends(get_api_token)):
    """Push a new event for a job"""
    # Verify API token has permission for this job
    if not auth_manager.verify_api_token_for_job(api_token, request.job_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    
    try:
        storage.store_event(
            job_id=request.job_id,
            event_type=request.type,
            message=request.message,
            info=request.info,
            extra=request.extra
        )
        
        return PushResponse(
            success=True,
            message="Event stored successfully",
            job_id=request.job_id,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error storing event for job {request.job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to store event")


# Push API Endpoints for Backup Data
@app.post("/api/push/status", response_model=PushResponse)
async def push_status(request: PushStatusRequest, api_token: str = Depends(get_api_token)):
    """Push backup run status and logs"""
    # Verify API token has permission for this job
    if not auth_manager.verify_api_token_for_job(api_token, request.job_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    
    try:
        # Store the backup run status and logs
        storage.store_backup_run(
            job_id=request.job_id,
            run_data={
                'run_id': request.run_id,
                'status': request.status,
                'start_time': request.start_time,
                'end_time': request.end_time,
                'exit_code': request.exit_code,
                'log_lines': request.log_lines,
                'error_message': request.error_message
            }
        )
        
        return PushResponse(
            success=True,
            message="Status and logs stored successfully",
            job_id=request.job_id,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error storing backup run status: {e}")
        raise HTTPException(status_code=500, detail="Failed to store backup status")


@app.post("/api/push/borg/info", response_model=PushResponse)
async def push_borg_info(request: BorgInfoRequest, api_token: str = Depends(get_api_token)):
    """Push Borg repository info and archive list"""
    # Verify API token has permission for this job
    if not auth_manager.verify_api_token_for_job(api_token, request.job_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    
    try:
        # Store repository info and archive list
        storage.store_borg_info(
            job_id=request.job_id,
            repository_info=request.repository_info,
            archive_list=request.archive_list
        )
        
        return PushResponse(
            success=True,
            message="Borg repository info and archives stored successfully",
            job_id=request.job_id,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error storing Borg info for job {request.job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to store Borg info")


@app.post("/api/push/borgmatic/info", response_model=PushResponse)
async def push_borgmatic_info(request: BorgmaticInfoRequest, api_token: str = Depends(get_api_token)):
    """Push Borgmatic repository info"""
    # Verify API token has permission for this job
    if not auth_manager.verify_api_token_for_job(api_token, request.job_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    
    try:
        # Handle repository label filtering for multi-repo borgmatic setups
        filtered_data = request.info_data
        
        # If data is a list (multiple repositories)
        if isinstance(request.info_data, list):
            if len(request.info_data) > 1 and not request.repository_label:
                # Multiple repositories without a label - return error
                raise HTTPException(
                    status_code=400, 
                    detail="Multiple repositories found in borgmatic data. Please specify repository_label to select which one to use."
                )
            elif request.repository_label:
                # Filter by repository label
                filtered_data = storage.filter_borgmatic_data(request.info_data, request.repository_label)
                if not filtered_data:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Repository with label '{request.repository_label}' not found in borgmatic data"
                    )
            else:
                # Single repository or no label specified - use first one
                filtered_data = request.info_data[0] if request.info_data else {}
        
        storage.store_borgmatic_info(
            job_id=request.job_id,
            info_data=filtered_data
        )
        
        return PushResponse(
            success=True,
            message="Borgmatic repository info stored successfully",
            job_id=request.job_id,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error storing Borgmatic info for job {request.job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to store Borgmatic info")


@app.post("/api/push/borgmatic/rinfo", response_model=PushResponse)
async def push_borgmatic_rinfo(request: BorgmaticRinfoRequest, api_token: str = Depends(get_api_token)):
    """Push Borgmatic repository and archive info"""
    # Verify API token has permission for this job
    if not auth_manager.verify_api_token_for_job(api_token, request.job_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    
    try:
        # Handle repository label filtering for multi-repo borgmatic setups
        filtered_data = request.rinfo_data
        
        # If data is a list (multiple repositories)
        if isinstance(request.rinfo_data, list):
            if len(request.rinfo_data) > 1 and not request.repository_label:
                # Multiple repositories without a label - return error
                raise HTTPException(
                    status_code=400, 
                    detail="Multiple repositories found in borgmatic data. Please specify repository_label to select which one to use."
                )
            elif request.repository_label:
                # Filter by repository label
                filtered_data = storage.filter_borgmatic_data(request.rinfo_data, request.repository_label)
                if not filtered_data:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Repository with label '{request.repository_label}' not found in borgmatic data"
                    )
            else:
                # Single repository or no label specified - use first one
                filtered_data = request.rinfo_data[0] if request.rinfo_data else {}
        
        storage.store_borgmatic_rinfo(
            job_id=request.job_id,
            rinfo_data=filtered_data
        )
        
        return PushResponse(
            success=True,
            message="Borgmatic repository and archive info stored successfully",
            job_id=request.job_id,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error storing Borgmatic rinfo for job {request.job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to store Borgmatic rinfo")


# Legacy endpoints (for backward compatibility)
@app.post("/push/{job_id}/info")
async def push_job_info_legacy(job_id: str):
    """Legacy endpoint - use /api/push/borg/info or /api/push/borgmatic/info instead"""
    raise HTTPException(
        status_code=410, 
        detail="This endpoint is deprecated. Use /api/push/borg/info or /api/push/borgmatic/info instead"
    )


@app.post("/push/{job_id}/log")
async def push_job_log_legacy(job_id: str):
    """Legacy endpoint - use /api/push/status instead"""
    raise HTTPException(
        status_code=410, 
        detail="This endpoint is deprecated. Use /api/push/status instead"
    )


if __name__ == "__main__":
    import uvicorn
    
    # Load config for uvicorn
    config_path = os.environ.get("BORGDASH_CONFIG", "/config/config.toml")
    cfg = load_config(config_path)
    
    uvicorn.run(
        "main:app",
        host=cfg.server.host,
        port=cfg.server.port,
        reload=cfg.server.debug,
        log_level="info" if not cfg.server.debug else "debug"
    )
