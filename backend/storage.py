"""
Data storage management for BorgDash
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from models import JobSummary, Job, Archive, BackupRun, JobStats, BackupEvent
from config import Config, get_all_job_configs
from validation import ConfigValidator

logger = logging.getLogger(__name__)


class DataStorage:
    """Handles all data storage operations"""

    def __init__(self, config: Config):
        self.config = config
        self.data_dir = Path(config.server.data_dir)
        self.config_dir = Path(config.server.config_dir)


    def ensure_directories(self):
        """Ensure all required directories exist"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)


    def get_all_job_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all job configurations"""
        return get_all_job_configs(str(self.config_dir))


    def _get_latest_archive_date(self, job_id: str) -> Optional[str]:
        """Get the date of the latest archive for a job"""
        try:
            archives_file = self.data_dir / job_id / "archives.json"
            if not archives_file.exists():
                return None

            with open(archives_file, 'r') as f:
                archives_data = json.load(f)

            if not archives_data:
                return None

            # Find the latest archive by date
            latest_date = None

            for archive in archives_data:
                archive_date_str = archive.get('start') or archive.get('time')
                if archive_date_str:
                    try:
                        archive_date = datetime.fromisoformat(archive_date_str.replace('Z', '+00:00'))
                        if latest_date is None or archive_date > latest_date:
                            latest_date = archive_date
                    except (ValueError, TypeError):
                        continue

            return latest_date.isoformat() if latest_date else None

        except Exception as e:
            logger.error(f"Error getting latest archive date for {job_id}: {e}")
            return None


    def _calculate_schedule_status(self, last_backup_str: Optional[str], max_age: str) -> str:
        """Calculate schedule status based on last backup and max_age"""
        if not last_backup_str:
            return "unknown"

        try:
            last_backup = datetime.fromisoformat(last_backup_str.replace('Z', '+00:00'))
            if ConfigValidator.is_backup_overdue(last_backup, max_age):
                return "overdue"
            else:
                return "on-time"
        except (ValueError, TypeError):
            return "unknown"


    def get_all_jobs(self) -> List[JobSummary]:
        """Get all jobs with summary information - based on config files"""
        jobs = []
        job_configs = get_all_job_configs(str(self.config_dir))

        for job_id, config in job_configs.items():
            try:
                # Always create job entry if config exists, regardless of data availability
                summary_file = self.data_dir / job_id / "job_summary.json"
                cache_data = {}
                
                # Load data if available
                if summary_file.exists():
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)

                # Calculate current schedule status based on max_age and latest archive date
                max_age = config.get('max_age', '24h')

                # Get latest archive date for schedule calculations
                latest_archive_date = self._get_latest_archive_date(job_id)

                # Use latest archive date for schedule status, fall back to backup run date
                backup_time_for_schedule = latest_archive_date or cache_data.get('last_successful_backup') or cache_data.get('last_backup')
                schedule_status = self._calculate_schedule_status(backup_time_for_schedule, max_age)

                # Parse timestamps - use latest archive date as the primary lastBackup
                last_backup = None
                if latest_archive_date:
                    last_backup = datetime.fromisoformat(latest_archive_date.replace('Z', '+00:00'))
                elif cache_data.get('last_backup'):
                    last_backup = datetime.fromisoformat(cache_data['last_backup'])

                last_successful_backup = datetime.fromisoformat(cache_data['last_successful_backup']) if cache_data.get('last_successful_backup') else None

                job_summary = JobSummary(
                    jobId=job_id,
                    name=config.get('display_name', job_id),
                    status=cache_data.get('status', 'no-data'),
                    scheduleStatus=schedule_status,
                    lastBackup=last_backup,
                    lastBackupRelative=self._calculate_relative_time(last_backup),
                    lastSuccessfulBackup=last_successful_backup,
                    lastSuccessfulBackupRelative=self._calculate_relative_time(last_successful_backup),
                    tags=config.get('tags', []),
                    stats=JobStats(
                        archiveCount=cache_data.get('archive_count', 0),
                        fullSize=cache_data.get('full_size', '0 B'),
                        compressedSize=cache_data.get('compressed_size', '0 B'),
                        deduplicatedSize=cache_data.get('deduplicated_size', '0 B'),
                        compressionRatio=cache_data.get('compression_ratio', '0%')
                    )
                )
                jobs.append(job_summary)
            except Exception as e:
                logger.error(f"Error loading job {job_id}: {e}")

        return sorted(jobs, key=lambda x: x.name)


    def get_job_details(self, job_id: str) -> Optional[Job]:
        """Get detailed information for a specific job - based on config file"""
        job_configs = get_all_job_configs(str(self.config_dir))
        config = job_configs.get(job_id)

        if not config:
            return None

        try:
            # Always return job details if config exists, regardless of data availability
            summary_file = self.data_dir / job_id / "job_summary.json"
            cache_data = {}
            
            # Load data if available
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

            # Calculate current schedule status based on max_age and latest archive date
            max_age = config.get('max_age', '24h')

            # Get latest archive date for schedule calculations
            latest_archive_date = self._get_latest_archive_date(job_id)

            # Use latest archive date for schedule status, fall back to backup run date
            backup_time_for_schedule = latest_archive_date or cache_data.get('last_successful_backup') or cache_data.get('last_backup')
            schedule_status = self._calculate_schedule_status(backup_time_for_schedule, max_age)

            # Parse timestamps - use latest archive date as the primary lastBackup
            last_backup = None
            if latest_archive_date:
                last_backup = datetime.fromisoformat(latest_archive_date.replace('Z', '+00:00'))
            elif cache_data.get('last_backup'):
                last_backup = datetime.fromisoformat(cache_data['last_backup'])

            last_successful_backup = datetime.fromisoformat(cache_data['last_successful_backup']) if cache_data.get('last_successful_backup') else None

            return Job(
                jobId=job_id,
                name=config.get('display_name', job_id),
                status=cache_data.get('status', 'no-data'),
                scheduleStatus=schedule_status,
                lastBackup=last_backup,
                lastBackupRelative=self._calculate_relative_time(last_backup),
                lastSuccessfulBackup=last_successful_backup,
                lastSuccessfulBackupRelative=self._calculate_relative_time(last_successful_backup),
                tags=config.get('tags', []),
                description=config.get('description'),
                backupType=config.get('backup_type', 'borgmatic'),
                maxAge=max_age,
                stats=JobStats(
                    archiveCount=cache_data.get('archive_count', 0),
                    fullSize=cache_data.get('full_size', '0 B'),
                    compressedSize=cache_data.get('compressed_size', '0 B'),
                    deduplicatedSize=cache_data.get('deduplicated_size', '0 B'),
                    compressionRatio=cache_data.get('compression_ratio', '0%')
                ),
                config=config
            )
        except Exception as e:
            logger.error(f"Error loading job details for {job_id}: {e}")
            return None


    def get_job_archives(self, job_id: str, offset: int = 0, limit: int = 15, sort_by: str = "date", sort_order: str = "desc") -> Optional[Dict[str, Any]]:
        """Get archives for a job with pagination and sorting"""
        try:
            archives_file = self.data_dir / job_id / "archives.json"
            if not archives_file.exists():
                logger.warning(f"Archives file not found for job {job_id}: {archives_file}")
                return None

            with open(archives_file, 'r') as f:
                archives_data = json.load(f)

            logger.info(f"Loaded {len(archives_data)} archives for job {job_id}")
            
            # Sort archives before pagination
            def sort_key(archive):
                if sort_by == "date":
                    return datetime.fromisoformat(archive['start']) if archive.get('start') else datetime.min
                elif sort_by == "name":
                    return archive['name'].lower()
                elif sort_by in ["originalSize", "compressedSize", "deduplicatedSize"]:
                    # Get size value for sorting
                    size_value = 0
                    if 'stats' in archive:
                        stats = archive['stats']
                        if sort_by == "originalSize" and 'original_size' in stats:
                            size_value = stats['original_size']
                        elif sort_by == "compressedSize" and 'compressed_size' in stats:
                            size_value = stats['compressed_size']
                        elif sort_by == "deduplicatedSize" and 'deduplicated_size' in stats:
                            size_value = stats['deduplicated_size']
                    elif sort_by == "originalSize" and 'original_size' in archive:
                        size_value = archive['original_size'] if isinstance(archive['original_size'], int) else 0
                    elif sort_by == "compressedSize" and 'compressed_size' in archive:
                        size_value = archive['compressed_size'] if isinstance(archive['compressed_size'], int) else 0
                    elif sort_by == "deduplicatedSize" and 'deduplicated_size' in archive:
                        size_value = archive['deduplicated_size'] if isinstance(archive['deduplicated_size'], int) else 0
                    return size_value
                return ""
            
            archives_data.sort(key=sort_key, reverse=(sort_order == "desc"))
            
            total = len(archives_data)

            # Apply pagination after sorting
            paginated_archives = archives_data[offset:offset + limit]

            archives = []
            for archive in paginated_archives:
                # Check if individual archive size data is available
                original_size = "n/a"
                compressed_size = "n/a"
                deduplicated_size = "n/a"

                # Check if archive has size statistics (from borgmatic data)
                if 'stats' in archive:
                    stats = archive['stats']
                    if 'original_size' in stats:
                        original_size = self._format_size(stats['original_size'])
                    if 'compressed_size' in stats:
                        compressed_size = self._format_size(stats['compressed_size'])
                    if 'deduplicated_size' in stats:
                        deduplicated_size = self._format_size(stats['deduplicated_size'])
                elif any(key in archive for key in ['original_size', 'compressed_size', 'deduplicated_size']):
                    # Handle direct size fields (if they exist)
                    if 'original_size' in archive:
                        original_size = self._format_size(archive['original_size']) if isinstance(archive['original_size'], int) else str(archive['original_size'])
                    if 'compressed_size' in archive:
                        compressed_size = self._format_size(archive['compressed_size']) if isinstance(archive['compressed_size'], int) else str(archive['compressed_size'])
                    if 'deduplicated_size' in archive:
                        deduplicated_size = self._format_size(archive['deduplicated_size']) if isinstance(archive['deduplicated_size'], int) else str(archive['deduplicated_size'])

                archives.append(Archive(
                    name=archive['name'],
                    createdAt=datetime.fromisoformat(archive['start']) if archive.get('start') else datetime.now(),
                    originalSize=original_size,
                    compressedSize=compressed_size,
                    deduplicatedSize=deduplicated_size
                ))

            has_more = offset + limit < total
            next_offset = offset + limit if has_more else None

            result = {
                "items": archives,
                "total": total,
                "hasMore": has_more,
                "nextOffset": next_offset
            }

            logger.info(f"Returning {len(archives)} archives for job {job_id}")
            return result

        except Exception as e:
            logger.error(f"Error loading archives for job {job_id}: {e}")
            return None


    def get_job_runs(self, job_id: str, limit: int = 15) -> Optional[List[BackupRun]]:
        """Get recent backup runs for a job"""
        try:
            runs_file = self.data_dir / job_id / "runs.json"
            if not runs_file.exists():
                return []

            with open(runs_file, 'r') as f:
                runs_data = json.load(f)

            runs_list = runs_data.get('runs', [])

            # Sort by timestamp (newest first) and limit
            sorted_runs = sorted(runs_list, key=lambda x: x['timestamp'], reverse=True)[:limit]

            return [
                BackupRun(
                    id=run['id'],
                    status=run['status'],
                    timestamp=datetime.fromisoformat(run['timestamp']) if run['timestamp'] else None,
                    timestampRelative=self._calculate_relative_time(
                        datetime.fromisoformat(run['timestamp']) if run['timestamp'] else None
                    ),
                    duration=run.get('duration'),
                    endTimestamp=datetime.fromisoformat(run['end_timestamp']) if run.get('end_timestamp') else None
                )
                for run in sorted_runs
            ]

        except Exception as e:
            logger.error(f"Error loading runs for job {job_id}: {e}")
            return []


    def get_run_details(self, job_id: str, run_id: str, offset: int = 0, limit: int = 50) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific run including logs"""
        try:
            # First get run metadata
            runs_file = self.data_dir / job_id / "runs.json"
            if not runs_file.exists():
                return None

            with open(runs_file, 'r') as f:
                runs_data = json.load(f)

            run_info = None
            for run in runs_data.get('runs', []):
                if run['id'] == run_id:
                    run_info = run
                    break

            if not run_info:
                return None

            # Get log file
            log_file = self.data_dir / job_id / f"run_{run_id}.log"
            log_lines = []
            total_lines = 0

            if log_file.exists():
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    total_lines = len(all_lines)
                    log_lines = [line.rstrip() for line in all_lines[offset:offset + limit]]

            has_more = offset + limit < total_lines
            next_offset = offset + limit if has_more else None

            return {
                "id": run_info['id'],
                "status": run_info['status'],
                "timestamp": datetime.fromisoformat(run_info['timestamp']) if run_info['timestamp'] else None,
                "duration": run_info.get('duration'),
                "endTimestamp": datetime.fromisoformat(run_info['end_timestamp']) if run_info.get('end_timestamp') else None,
                "logLines": log_lines,
                "totalLines": total_lines,
                "hasMore": has_more,
                "nextOffset": next_offset
            }

        except Exception as e:
            logger.error(f"Error loading run details for {job_id}/{run_id}: {e}")
            return None


    # Push API Methods
    def store_backup_run(self, job_id: str, run_data: Dict[str, Any]):
        """Store backup run status and logs from push API"""
        try:
            job_dir = self.data_dir / job_id
            job_dir.mkdir(parents=True, exist_ok=True)

            # Store the run data
            run_file = job_dir / f"run_{run_data['run_id']}.json"

            # Calculate duration if both timestamps are available
            duration = None
            if run_data.get('start_time') and run_data.get('end_time'):
                start_time = run_data['start_time']
                end_time = run_data['end_time']
                duration_seconds = int((end_time - start_time).total_seconds())
                duration = f"{duration_seconds}s"

            run_info = {
                "id": run_data['run_id'],
                "status": run_data['status'],
                "timestamp": run_data['start_time'].isoformat() if run_data['start_time'] else None,
                "end_timestamp": run_data['end_time'].isoformat() if run_data.get('end_time') else None,
                "exit_code": run_data.get('exit_code'),
                "error_message": run_data.get('error_message'),
                "duration": duration
            }

            with open(run_file, 'w') as f:
                json.dump(run_info, f, indent=2)

            # Store logs separately
            if run_data.get('log_lines'):
                log_file = job_dir / f"run_{run_data['run_id']}.log"
                with open(log_file, 'w') as f:
                    for line in run_data['log_lines']:
                        f.write(line + '\n')

            # Update job summary
            self._update_job_summary(job_id, run_data)

            logger.info(f"Stored backup run {run_data['run_id']} for job {job_id}")

        except Exception as e:
            logger.error(f"Error storing backup run for job {job_id}: {e}")
            raise


    def _extract_repository_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract repository info from borgmatic/borg data in unified format"""
        repository_info = {}

        # Copy repository info
        if 'repository' in data:
            repository_info['repository'] = data['repository']

        # Copy cache info if present
        if 'cache' in data:
            repository_info['cache'] = data['cache']

        # Copy encryption info if present
        if 'encryption' in data:
            repository_info['encryption'] = data['encryption']

        # Copy security_dir if present
        if 'security_dir' in data:
            repository_info['security_dir'] = data['security_dir']

        return repository_info

    def store_borg_info(self, job_id: str, repository_info: Dict[str, Any], archive_list: List[Dict[str, Any]]):
        """Store Borg repository info and archive list"""
        try:
            job_dir = self.data_dir / job_id
            job_dir.mkdir(parents=True, exist_ok=True)

            # Store repository info
            repo_file = job_dir / "repository_info.json"
            with open(repo_file, 'w', encoding='utf-8') as f:
                json.dump(repository_info, f, indent=2)
            logger.info(f"Stored repository_info.json for job {job_id}")

            # Store archive list
            archives_file = job_dir / "archives.json"
            with open(archives_file, 'w', encoding='utf-8') as f:
                json.dump(archive_list, f, indent=2)
            logger.info(f"Stored archives.json for job {job_id} with {len(archive_list)} archives")

            # Update cache.json with archive statistics
            self._update_summary_from_borg_info(job_id, repository_info, archive_list)

            logger.info(f"Successfully stored Borg info for job {job_id} with {len(archive_list)} archives")

        except Exception as e:
            logger.error(f"Error storing Borg info for job {job_id}: {e}")
            raise


    def store_borgmatic_info(self, job_id: str, info_data: Union[Dict[str, Any], List[Dict[str, Any]]]):
        """Store Borgmatic repository info in unified format"""
        try:
            job_dir = self.data_dir / job_id
            job_dir.mkdir(parents=True, exist_ok=True)

            # Extract repository info and archives from borgmatic data
            repository_info = {}
            archives = []
            repository_path = ""

            # Handle borgmatic data structure (can be list or dict)
            if isinstance(info_data, list) and info_data:
                first_repo = info_data[0]
                repository_info = self._extract_repository_info(first_repo)
                repository_path = first_repo.get('repository', {}).get('location', '')
                if 'archives' in first_repo:
                    archives = first_repo['archives']
            elif isinstance(info_data, dict):
                repository_info = self._extract_repository_info(info_data)
                repository_path = info_data.get('repository', {}).get('location', '')
                if 'archives' in info_data:
                    archives = info_data['archives']

            # Store in unified format - repository_info.json
            if repository_info:
                repo_file = job_dir / "repository_info.json"
                with open(repo_file, 'w', encoding='utf-8') as f:
                    json.dump(repository_info, f, indent=2)
                logger.info(f"Stored repository_info.json for job {job_id}")

            # Store in unified format - archives.json
            if archives:
                archives_file = job_dir / "archives.json"
                with open(archives_file, 'w', encoding='utf-8') as f:
                    json.dump(archives, f, indent=2)
                logger.info(f"Stored archives.json for job {job_id} with {len(archives)} archives")

            # Update cache if we have archive and repository information
            if archives and repository_info:
                # Use the actual repository info with cache stats
                self._update_summary_from_borg_info(job_id, repository_info, archives)
            elif archives:
                # Fallback if we only have archives
                dummy_repo_info = {'repository': {'location': repository_path}}
                self._update_summary_from_borg_info(job_id, dummy_repo_info, archives)

            logger.info(f"Stored Borgmatic info for job {job_id} in unified format")

        except Exception as e:
            logger.error(f"Error storing Borgmatic info for job {job_id}: {e}")
            raise


    def store_borgmatic_rinfo(self, job_id: str, rinfo_data: Union[Dict[str, Any], List[Dict[str, Any]]]):
        """Store Borgmatic repository and archive info in unified format"""
        try:
            job_dir = self.data_dir / job_id
            job_dir.mkdir(parents=True, exist_ok=True)

            # Extract repository info and archives from borgmatic rinfo data
            repository_info = {}
            archives = []
            repository_path = ""

            # Handle borgmatic rinfo structure (can be list or dict)
            if isinstance(rinfo_data, list):
                for repo_info in rinfo_data:
                    if 'archives' in repo_info:
                        archives.extend(repo_info['archives'])
                    # Use first repo for repository info
                    if not repository_info and repo_info:
                        repository_info = self._extract_repository_info(repo_info)
                        repository_path = repo_info.get('repository', {}).get('location', '')
            elif isinstance(rinfo_data, dict):
                repository_info = self._extract_repository_info(rinfo_data)
                repository_path = rinfo_data.get('repository', {}).get('location', '')
                if 'archives' in rinfo_data:
                    archives = rinfo_data['archives']

            # Store in unified format - repository_info.json
            if repository_info:
                repo_file = job_dir / "repository_info.json"
                with open(repo_file, 'w', encoding='utf-8') as f:
                    json.dump(repository_info, f, indent=2)
                logger.info(f"Stored repository_info.json for job {job_id}")

            # Store in unified format - archives.json
            if archives:
                archives_file = job_dir / "archives.json"
                with open(archives_file, 'w', encoding='utf-8') as f:
                    json.dump(archives, f, indent=2)
                logger.info(f"Stored archives.json for job {job_id} with {len(archives)} archives")

            # Update cache with archive information
            if archives and repository_info:
                self._update_summary_from_borg_info(job_id, repository_info, archives)

            logger.info(f"Stored Borgmatic rinfo for job {job_id} in unified format with {len(archives)} archives")

        except Exception as e:
            logger.error(f"Error storing Borgmatic rinfo for job {job_id}: {e}")
            raise


    def filter_borgmatic_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], repository_label: str) -> Dict[str, Any]:
        """Filter Borgmatic data for a specific repository label"""
        try:
            if not repository_label:
                # If no label specified, return first item if it's a list, or the dict itself
                if isinstance(data, list):
                    return data[0] if data else {}
                return data

            # If data is a list (multiple repositories)
            if isinstance(data, list):
                for repo_data in data:
                    if isinstance(repo_data, dict) and repo_data.get('repository', {}).get('label') == repository_label:
                        return repo_data
                # If no match found, return first repo or empty dict
                return data[0] if data else {}

            # If data is a dict, check if it matches the label
            elif isinstance(data, dict):
                repo_label = data.get('repository', {}).get('label')
                if repo_label == repository_label or not repo_label:
                    return data
                # If it doesn't match and we have multiple repos nested, try to find it
                if 'repositories' in data:
                    for repo_data in data['repositories']:
                        if isinstance(repo_data, dict) and repo_data.get('repository', {}).get('label') == repository_label:
                            return repo_data

            return {} if isinstance(data, list) else data

        except Exception as e:
            logger.error(f"Error filtering Borgmatic data: {e}")
            return {} if isinstance(data, list) else data


    def _update_job_summary(self, job_id: str, run_data: Dict[str, Any]):
        """Update job summary with latest run information"""
        try:
            job_dir = self.data_dir / job_id
            summary_file = job_dir / "summary.json"

            # Load existing summary or create new
            summary = {}
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    summary = json.load(f)

            # Update with latest run info
            summary.update({
                'job_id': job_id,
                'last_run': run_data['start_time'].isoformat() if run_data.get('start_time') else None,
                'last_status': run_data['status'],
                'last_updated': datetime.now().isoformat()
            })

            # Save updated summary
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)

            # Also update job_summary.json and runs.json
            self._update_summary_from_run(job_id, run_data)
            self._update_runs_from_run(job_id, run_data)

        except Exception as e:
            logger.error(f"Error updating job summary for {job_id}: {e}")


    def _update_summary_from_run(self, job_id: str, run_data: Dict[str, Any]):
        """Update job_summary.json with latest run information"""
        try:
            job_dir = self.data_dir / job_id
            summary_file = job_dir / "job_summary.json"

            # Load existing summary or create new
            cache_data = {}
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

            # Update with latest run info
            now = datetime.now().isoformat()
            cache_data.update({
                'job_id': job_id,
                'last_updated': now
            })

            # Update last_backup timestamp
            if run_data.get('start_time'):
                cache_data['last_backup'] = run_data['start_time'].isoformat()

            # Update last_successful_backup if status is success
            if run_data.get('status') == 'success' and run_data.get('start_time'):
                cache_data['last_successful_backup'] = run_data['start_time'].isoformat()

            # Update status based on run status
            if run_data.get('status'):
                cache_data['status'] = run_data['status']

            # Preserve existing archive stats if not updated
            cache_data.setdefault('archive_count', 0)
            cache_data.setdefault('full_size', '0 B')
            cache_data.setdefault('compressed_size', '0 B')
            cache_data.setdefault('deduplicated_size', '0 B')
            cache_data.setdefault('compression_ratio', '0%')
            cache_data.setdefault('repository_path', '')
            cache_data.setdefault('backup_type', 'borgmatic')

            # Save updated summary
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)

        except Exception as e:
            logger.error(f"Error updating summary for {job_id}: {e}")


    def _update_runs_from_run(self, job_id: str, run_data: Dict[str, Any]):
        """Update runs.json with latest run information"""
        try:
            job_dir = self.data_dir / job_id
            runs_file = job_dir / "runs.json"

            # Load existing runs or create new
            runs_data = {'runs': []}
            if runs_file.exists():
                with open(runs_file, 'r') as f:
                    runs_data = json.load(f)

            # Create run entry
            run_entry = {
                'id': run_data['run_id'],
                'status': run_data['status'],
                'timestamp': run_data['start_time'].isoformat() if run_data.get('start_time') else None,
                'end_timestamp': run_data['end_time'].isoformat() if run_data.get('end_time') else None,
                'exit_code': run_data.get('exit_code'),
                'error_message': run_data.get('error_message')
            }

            # Calculate duration if both timestamps exist
            if run_data.get('start_time') and run_data.get('end_time'):
                duration = (run_data['end_time'] - run_data['start_time']).total_seconds()
                run_entry['duration'] = f"{int(duration)}s"

            # Update or add run (check if run_id already exists)
            runs_list = runs_data.get('runs', [])
            updated = False
            for i, existing_run in enumerate(runs_list):
                if existing_run.get('id') == run_data['run_id']:
                    runs_list[i] = run_entry
                    updated = True
                    break

            if not updated:
                runs_list.append(run_entry)

            # Keep only the most recent 100 runs (sorted by timestamp)
            runs_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            runs_data['runs'] = runs_list[:100]

            # Save updated runs
            with open(runs_file, 'w') as f:
                json.dump(runs_data, f, indent=2)

        except Exception as e:
            logger.error(f"Error updating runs for {job_id}: {e}")


    def _update_summary_from_borg_info(self, job_id: str, repository_info: Dict[str, Any], archive_list: List[Dict[str, Any]]):
        """Update job_summary.json with Borg repository and archive statistics"""
        try:
            job_dir = self.data_dir / job_id
            summary_file = job_dir / "job_summary.json"

            # Load existing summary or create new
            cache_data = {}
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

            # Update archive count
            cache_data['archive_count'] = len(archive_list)

            # Calculate size statistics from repository info
            repo_stats = repository_info.get('cache', {}).get('stats', {})
            if repo_stats:
                # Format sizes (convert bytes to human readable)
                total_size = repo_stats.get('total_size', 0)
                compressed_size = repo_stats.get('total_csize', 0)
                deduplicated_size = repo_stats.get('unique_size', 0)

                cache_data['full_size'] = self._format_size(total_size)
                cache_data['compressed_size'] = self._format_size(compressed_size)
                cache_data['deduplicated_size'] = self._format_size(deduplicated_size)

                # Calculate compression ratio
                if total_size > 0 and compressed_size > 0:
                    ratio = (1 - compressed_size / total_size) * 100
                    cache_data['compression_ratio'] = f"{ratio:.1f}%"
                else:
                    cache_data['compression_ratio'] = "0%"

            # Update repository path if available
            if 'repository' in repository_info and 'location' in repository_info['repository']:
                cache_data['repository_path'] = repository_info['repository']['location']

            # Update timestamp
            cache_data['last_updated'] = datetime.now().isoformat()

            # Preserve job_id and other fields
            cache_data['job_id'] = job_id
            cache_data.setdefault('backup_type', 'borgmatic')
            cache_data.setdefault('status', 'unknown')
            cache_data.setdefault('schedule_status', 'unknown')

            # Save updated summary
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)

        except Exception as e:
            logger.error(f"Error updating summary from Borg info for {job_id}: {e}")


    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable format"""
        if size_bytes == 0:
            return "0 B"

        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


    def _calculate_relative_time(self, timestamp: Optional[datetime]) -> Optional[str]:
        """Calculate relative time string (e.g., '2 days ago', '3 hours ago')"""
        if not timestamp:
            return None

        now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
        diff = now - timestamp

        # Calculate total seconds
        total_seconds = diff.total_seconds()

        if total_seconds < 0:
            return "in the future"

        # Less than a minute
        if total_seconds < 60:
            return "just now"

        # Less than an hour
        if total_seconds < 3600:
            minutes = int(total_seconds // 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"

        # Less than a day
        if total_seconds < 86400:
            hours = int(total_seconds // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"

        # Less than a week
        if total_seconds < 604800:
            days = int(total_seconds // 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"

        # Less than a month (30 days)
        if total_seconds < 2592000:
            weeks = int(total_seconds // 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"

        # Less than a year
        if total_seconds < 31536000:
            months = int(total_seconds // 2592000)
            return f"{months} month{'s' if months != 1 else ''} ago"

        # More than a year
        years = int(total_seconds // 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


    # Event Storage Methods
    def store_event(self, job_id: str, event_type: str, message: str, info: Optional[str] = None, extra: Optional[Dict[str, Any]] = None) -> str:
        """Store a new event for a job"""
        try:
            job_dir = self.data_dir / job_id
            job_dir.mkdir(parents=True, exist_ok=True)

            # Generate event ID and timestamp
            now = datetime.now()
            event_id = f"{now.isoformat()}_{uuid.uuid4().hex[:8]}"
            
            # Create event data
            event_data = {
                "id": event_id,
                "type": event_type,
                "timestamp": now.isoformat(),
                "message": message,
                "has_info": info is not None,
                "extra": extra or {}
            }

            # Store event JSON
            event_file = job_dir / f"event_{event_id}.json"
            with open(event_file, 'w', encoding='utf-8') as f:
                json.dump(event_data, f, indent=2)

            # Store info file if provided
            if info:
                info_file = job_dir / f"event_{event_id}.info"
                with open(info_file, 'w', encoding='utf-8') as f:
                    f.write(info)

            logger.info(f"Stored event {event_id} for job {job_id}")

            # Update job summary based on event
            self._update_summary_from_event(job_id, event_type, now, extra)

            return event_id

        except Exception as e:
            logger.error(f"Error storing event for job {job_id}: {e}")
            raise


    def get_job_events(self, job_id: str, offset: int = 0, limit: int = 15) -> Optional[Dict[str, Any]]:
        """Get events for a job with pagination (sorted by timestamp desc)"""
        try:
            job_dir = self.data_dir / job_id
            if not job_dir.exists():
                return {"items": [], "total": 0, "hasMore": False, "nextOffset": None}

            # Find all event files and load their timestamps for proper sorting
            event_files = list(job_dir.glob("event_*.json"))
            
            # Load events with their timestamps for sorting
            events_with_timestamps = []
            for event_file in event_files:
                try:
                    with open(event_file, 'r', encoding='utf-8') as f:
                        event_data = json.load(f)
                    timestamp = datetime.fromisoformat(event_data['timestamp'])
                    events_with_timestamps.append((event_file, timestamp, event_data))
                except Exception as e:
                    logger.error(f"Error loading event file {event_file}: {e}")
                    continue

            # Sort by timestamp (newest first)
            events_with_timestamps.sort(key=lambda x: x[1], reverse=True)
            
            total = len(events_with_timestamps)
            paginated_events = events_with_timestamps[offset:offset + limit]

            events = []
            for event_file, timestamp, event_data in paginated_events:
                events.append(BackupEvent(
                    id=event_data['id'],
                    type=event_data['type'],
                    timestamp=timestamp,
                    timestampRelative=self._calculate_relative_time(timestamp),
                    message=event_data['message'],
                    hasInfo=event_data.get('has_info', False),
                    extra=event_data.get('extra', {})
                ))

            has_more = offset + limit < total
            next_offset = offset + limit if has_more else None

            return {
                "items": events,
                "total": total,
                "hasMore": has_more,
                "nextOffset": next_offset
            }

        except Exception as e:
            logger.error(f"Error loading events for job {job_id}: {e}")
            return None


    def get_event_info(self, job_id: str, event_id: str, offset: int = 0, limit: int = 50) -> Optional[Dict[str, Any]]:
        """Get info content for a specific event with pagination"""
        try:
            job_dir = self.data_dir / job_id
            info_file = job_dir / f"event_{event_id}.info"
            
            if not info_file.exists():
                return None

            with open(info_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                total_lines = len(all_lines)
                log_lines = [line.rstrip() for line in all_lines[offset:offset + limit]]

            has_more = offset + limit < total_lines
            next_offset = offset + limit if has_more else None

            return {
                "lines": log_lines,
                "totalLines": total_lines,
                "hasMore": has_more,
                "nextOffset": next_offset
            }

        except Exception as e:
            logger.error(f"Error loading event info for {job_id}/{event_id}: {e}")
            return None


    def _update_summary_from_event(self, job_id: str, event_type: str, timestamp: datetime, extra: Optional[Dict[str, Any]] = None):
        """Update job summary based on new event"""
        try:
            job_dir = self.data_dir / job_id
            summary_file = job_dir / "job_summary.json"

            # Load existing summary or create new
            cache_data = {}
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

            # Update based on event type - only consider "everything" action for overall status
            action = extra.get('action') if extra else None
            
            if event_type in ['success', 'failed'] and action == 'everything':
                # Update status based on last success/failed event with "everything" action
                cache_data['status'] = event_type
                cache_data['last_backup'] = timestamp.isoformat()
                
                if event_type == 'success':
                    cache_data['last_successful_backup'] = timestamp.isoformat()

            # Update last updated timestamp
            cache_data['last_updated'] = datetime.now().isoformat()
            cache_data['job_id'] = job_id

            # Preserve existing fields
            cache_data.setdefault('archive_count', 0)
            cache_data.setdefault('full_size', '0 B')
            cache_data.setdefault('compressed_size', '0 B')
            cache_data.setdefault('deduplicated_size', '0 B')
            cache_data.setdefault('compression_ratio', '0%')
            cache_data.setdefault('repository_path', '')
            cache_data.setdefault('backup_type', 'borgmatic')

            # Save updated summary
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)

        except Exception as e:
            logger.error(f"Error updating summary from event for {job_id}: {e}")
