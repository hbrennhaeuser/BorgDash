"""
Configuration validation for BorgDash
"""

import re
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple
import toml


class ConfigValidationError(Exception):
    """Configuration validation error"""
    pass


class ConfigValidator:
    """Validates job configurations"""
    
    JOB_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    MAX_AGE_PATTERN = re.compile(r'^(\d+)([mhd])$')
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        # Generate a 32-character key with URL-safe characters
        alphabet = string.ascii_letters + string.digits + '-_'
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    @staticmethod
    def validate_job_id(job_id: str) -> bool:
        """Validate job ID format"""
        if not job_id:
            return False
        return bool(ConfigValidator.JOB_ID_PATTERN.match(job_id))
    
    @staticmethod
    def validate_max_age(max_age: str) -> bool:
        """Validate max_age format (e.g., 1d, 24h, 1440m)"""
        if not max_age:
            return False
        return bool(ConfigValidator.MAX_AGE_PATTERN.match(max_age))
    
    @staticmethod
    def parse_max_age_to_seconds(max_age: str) -> int:
        """Parse max_age string to seconds"""
        match = ConfigValidator.MAX_AGE_PATTERN.match(max_age)
        if not match:
            raise ValueError(f"Invalid max_age format: {max_age}")
        
        value, unit = match.groups()
        value = int(value)
        
        if unit == 'm':  # minutes
            return value * 60
        elif unit == 'h':  # hours
            return value * 3600
        elif unit == 'd':  # days
            return value * 86400
        else:
            raise ValueError(f"Invalid max_age unit: {unit}")
    
    @staticmethod
    def is_backup_overdue(last_backup: datetime, max_age: str) -> bool:
        """Check if backup is overdue based on max_age"""
        try:
            max_age_seconds = ConfigValidator.parse_max_age_to_seconds(max_age)
            cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)
            return last_backup < cutoff_time
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_backup_type(backup_type: str) -> bool:
        """Validate backup type"""
        return backup_type in ['borg', 'borgmatic']
    
    @staticmethod
    def validate_and_fix_job_config(config_data: Dict[str, Any], config_path: Path) -> Tuple[Dict[str, Any], bool]:
        """
        Validate and fix job configuration
        Returns: (fixed_config, was_modified)
        """
        modified = False
        fixed_config = config_data.copy()
        
        # Validate job_id
        job_id = fixed_config.get('job_id', '')
        if not ConfigValidator.validate_job_id(job_id):
            raise ConfigValidationError(
                f"Invalid job_id '{job_id}'. Must contain only a-zA-Z, 0-9, _, -"
            )
        
        # Validate and fix backup_type
        backup_type = fixed_config.get('backup_type', 'borgmatic')
        if not ConfigValidator.validate_backup_type(backup_type):
            fixed_config['backup_type'] = 'borgmatic'
            modified = True
        
        # Validate and fix max_age
        max_age = fixed_config.get('max_age', '24h')
        if not ConfigValidator.validate_max_age(max_age):
            fixed_config['max_age'] = '24h'
            modified = True
        
        # Generate API key if missing
        api_keys = fixed_config.get('api_keys', [])
        if not api_keys:
            new_key = ConfigValidator.generate_api_key()
            fixed_config['api_keys'] = [new_key]
            modified = True
        else:
            # Validate existing keys format (should be URL-safe)
            valid_keys = []
            for key in api_keys:
                if isinstance(key, str) and len(key) >= 16:  # Minimum length check
                    valid_keys.append(key)
                else:
                    # Replace invalid key
                    valid_keys.append(ConfigValidator.generate_api_key())
                    modified = True
            fixed_config['api_keys'] = valid_keys
        
        # Ensure required fields have defaults
        if 'display_name' not in fixed_config:
            fixed_config['display_name'] = job_id.replace('-', ' ').replace('_', ' ').title()
            modified = True
        
        if 'tags' not in fixed_config:
            fixed_config['tags'] = []
            modified = True
        
        # Write back if modified
        if modified:
            with open(config_path, 'w') as f:
                toml.dump(fixed_config, f)
        
        return fixed_config, modified
    
    @staticmethod
    def validate_all_configs(config_dir: Path) -> Dict[str, Dict[str, Any]]:
        """
        Validate all job configurations and check for duplicates
        Returns: Dict of valid configurations
        """
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
            return {}
        
        valid_configs = {}
        seen_job_ids = set()
        errors = []
        
        for config_file in config_dir.glob("*.toml"):
            try:
                with open(config_file, 'r') as f:
                    config_data = toml.load(f)
                
                # Validate and fix configuration
                fixed_config, was_modified = ConfigValidator.validate_and_fix_job_config(
                    config_data, config_file
                )
                
                job_id = fixed_config['job_id']
                
                # Check for duplicate job IDs
                if job_id in seen_job_ids:
                    errors.append(f"Duplicate job_id '{job_id}' found in {config_file.name}")
                    continue
                
                seen_job_ids.add(job_id)
                valid_configs[job_id] = fixed_config
                
                if was_modified:
                    print(f"Fixed configuration for job '{job_id}' in {config_file.name}")
                
            except Exception as e:
                errors.append(f"Error in {config_file.name}: {str(e)}")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(errors)
            raise ConfigValidationError(error_msg)
        
        return valid_configs


def validate_configs(config_dir: str) -> Dict[str, Dict[str, Any]]:
    """
    Main function to validate all configurations
    """
    config_path = Path(config_dir)
    validator = ConfigValidator()
    return validator.validate_all_configs(config_path)
