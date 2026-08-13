"""
File-based profile storage and retrieval.
Validates: Requirement 6
"""

import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np


class ProfileStore:
    """
    File-based persistence layer for voiceprint profiles.
    
    Each profile is stored in a dedicated directory:
    profiles/{name}/
        ├── voiceprint.npy    # 192-dim embedding vector
        └── meta.json         # Profile metadata
    
    Implements atomic writes using temporary files + rename to prevent corruption.
    """
    
    # Valid profile name pattern: alphanumeric, underscore, hyphen (1-64 chars)
    VALID_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')
    
    def __init__(self, base_path: str = "profiles"):
        """
        Initialize profile store with base directory.
        
        Args:
            base_path: Base directory for all profile storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _validate_profile_name(self, name: str) -> bool:
        """
        Validate profile name for security and format compliance.
        
        Args:
            name: Profile name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not name or not isinstance(name, str):
            return False
        
        # Check pattern match
        if not self.VALID_NAME_PATTERN.match(name):
            return False
        
        # Prevent path traversal
        if '..' in name or '/' in name or '\\' in name:
            return False
        
        return True
    
    def _get_profile_dir(self, name: str) -> Path:
        """Get profile directory path."""
        return self.base_path / name
    
    def _get_voiceprint_path(self, name: str) -> Path:
        """Get voiceprint file path."""
        return self._get_profile_dir(name) / "voiceprint.npy"
    
    def _get_metadata_path(self, name: str) -> Path:
        """Get metadata file path."""
        return self._get_profile_dir(name) / "meta.json"
    
    def profile_exists(self, name: str) -> bool:
        """
        Check if profile exists.
        
        Args:
            name: Profile name
            
        Returns:
            True if profile exists, False otherwise
        """
        if not self._validate_profile_name(name):
            return False
        
        profile_dir = self._get_profile_dir(name)
        voiceprint_path = self._get_voiceprint_path(name)
        metadata_path = self._get_metadata_path(name)
        
        return (profile_dir.exists() and 
                voiceprint_path.exists() and 
                metadata_path.exists())
    
    def create_profile(self, name: str, voiceprint: np.ndarray, metadata: dict) -> bool:
        """
        Create new profile with voiceprint and metadata.
        
        Uses atomic write strategy:
        1. Write to temporary file
        2. Atomic rename after successful write
        
        Args:
            name: Profile name
            voiceprint: 192-dimensional embedding vector
            metadata: Profile metadata dict
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If profile name is invalid or profile already exists
            IOError: If file write fails
        """
        # Validate profile name
        if not self._validate_profile_name(name):
            raise ValueError(f"Invalid profile name: {name}. Must match pattern: {self.VALID_NAME_PATTERN.pattern}")
        
        # Check if profile already exists
        if self.profile_exists(name):
            raise ValueError(f"Profile '{name}' already exists")
        
        # Validate voiceprint shape
        if not isinstance(voiceprint, np.ndarray):
            raise ValueError("Voiceprint must be a numpy array")
        
        if voiceprint.shape != (192,):
            raise ValueError(f"Voiceprint must be 192-dimensional, got shape {voiceprint.shape}")
        
        # Create profile directory
        profile_dir = self._get_profile_dir(name)
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Atomic write for voiceprint
            voiceprint_path = self._get_voiceprint_path(name)
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, 
                                            dir=profile_dir, suffix='.tmp') as tmp_file:
                tmp_path = Path(tmp_file.name)
                np.save(tmp_file, voiceprint)
            
            # Atomic rename
            tmp_path.replace(voiceprint_path)
            
            # Atomic write for metadata
            metadata_path = self._get_metadata_path(name)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, 
                                            dir=profile_dir, suffix='.tmp', 
                                            encoding='utf-8') as tmp_file:
                tmp_path = Path(tmp_file.name)
                json.dump(metadata, tmp_file, indent=2)
            
            # Atomic rename
            tmp_path.replace(metadata_path)
            
            return True
            
        except Exception as e:
            # Clean up on failure
            if profile_dir.exists():
                shutil.rmtree(profile_dir, ignore_errors=True)
            raise IOError(f"Failed to create profile '{name}': {str(e)}")
    
    def get_profile(self, name: str) -> Optional[dict]:
        """
        Retrieve profile by name.
        
        Args:
            name: Profile name
            
        Returns:
            Dict with keys: 'name', 'voiceprint', 'metadata'
            None if profile doesn't exist
        """
        if not self._validate_profile_name(name):
            return None
        
        if not self.profile_exists(name):
            return None
        
        try:
            # Load voiceprint
            voiceprint_path = self._get_voiceprint_path(name)
            voiceprint = np.load(voiceprint_path)
            
            # Load metadata
            metadata_path = self._get_metadata_path(name)
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return {
                'name': name,
                'voiceprint': voiceprint,
                'metadata': metadata
            }
            
        except Exception as e:
            raise IOError(f"Failed to load profile '{name}': {str(e)}")
    
    def list_profiles(self) -> list[dict]:
        """
        List all profiles with metadata.
        
        Returns:
            List of dicts, each containing profile name and metadata
        """
        profiles = []
        
        if not self.base_path.exists():
            return profiles
        
        for profile_dir in self.base_path.iterdir():
            if not profile_dir.is_dir():
                continue
            
            name = profile_dir.name
            
            # Validate name and check if profile is complete
            if not self._validate_profile_name(name):
                continue
            
            if not self.profile_exists(name):
                continue
            
            try:
                # Load metadata only (not full voiceprint for performance)
                metadata_path = self._get_metadata_path(name)
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                profiles.append({
                    'name': name,
                    'metadata': metadata
                })
                
            except Exception:
                # Skip profiles with corrupted metadata
                continue
        
        return profiles
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete profile and all associated files.
        
        Args:
            name: Profile name
            
        Returns:
            True if deleted, False if profile doesn't exist
            
        Raises:
            IOError: If deletion fails
        """
        if not self._validate_profile_name(name):
            return False
        
        if not self.profile_exists(name):
            return False
        
        try:
            profile_dir = self._get_profile_dir(name)
            shutil.rmtree(profile_dir)
            return True
            
        except Exception as e:
            raise IOError(f"Failed to delete profile '{name}': {str(e)}")
    
    def update_threshold(self, name: str, threshold: float) -> bool:
        """
        Update profile-specific threshold in metadata.
        
        Args:
            name: Profile name
            threshold: New threshold value (0.0 - 1.0)
            
        Returns:
            True if updated, False if profile doesn't exist
            
        Raises:
            ValueError: If threshold is out of range
            IOError: If update fails
        """
        if not self._validate_profile_name(name):
            return False
        
        if not self.profile_exists(name):
            return False
        
        # Validate threshold range
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"Threshold must be in range [0.0, 1.0], got {threshold}")
        
        try:
            # Load existing metadata
            metadata_path = self._get_metadata_path(name)
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Update threshold
            metadata['threshold'] = threshold
            
            # Atomic write
            profile_dir = self._get_profile_dir(name)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, 
                                            dir=profile_dir, suffix='.tmp',
                                            encoding='utf-8') as tmp_file:
                tmp_path = Path(tmp_file.name)
                json.dump(metadata, tmp_file, indent=2)
            
            # Atomic rename
            tmp_path.replace(metadata_path)
            
            return True
            
        except Exception as e:
            raise IOError(f"Failed to update threshold for profile '{name}': {str(e)}")
