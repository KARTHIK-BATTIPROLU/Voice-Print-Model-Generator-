"""
Unit tests for ProfileStore class.
Tests profile creation, retrieval, deletion, and threshold updates.
"""

import json
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import numpy as np

from profile_store import ProfileStore


class TestProfileStore(unittest.TestCase):
    """Test suite for ProfileStore class."""
    
    def setUp(self):
        """Create temporary directory for test profiles."""
        self.test_dir = tempfile.mkdtemp()
        self.store = ProfileStore(base_path=self.test_dir)
        
        # Sample voiceprint and metadata
        self.sample_voiceprint = np.random.randn(192).astype(np.float32)
        self.sample_voiceprint = self.sample_voiceprint / np.linalg.norm(self.sample_voiceprint)
        
        self.sample_metadata = {
            "created": datetime.utcnow().isoformat() + "Z",
            "sample_count": 25,
            "threshold": 0.7,
            "intra_class_stats": {
                "mean_similarity": 0.85,
                "std_similarity": 0.05,
                "min_similarity": 0.72,
                "max_similarity": 0.95
            },
            "outliers_detected": [3, 17],
            "last_verified": None,
            "version": "1.0"
        }
    
    def tearDown(self):
        """Clean up temporary directory."""
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_profile_store_initialization(self):
        """Test ProfileStore initializes and creates base directory."""
        self.assertTrue(Path(self.test_dir).exists())
        self.assertTrue(Path(self.test_dir).is_dir())
    
    def test_create_profile_success(self):
        """Test successful profile creation."""
        result = self.store.create_profile(
            name="test_user",
            voiceprint=self.sample_voiceprint,
            metadata=self.sample_metadata
        )
        
        self.assertTrue(result)
        self.assertTrue(self.store.profile_exists("test_user"))
        
        # Verify files exist
        profile_dir = Path(self.test_dir) / "test_user"
        self.assertTrue(profile_dir.exists())
        self.assertTrue((profile_dir / "voiceprint.npy").exists())
        self.assertTrue((profile_dir / "meta.json").exists())
    
    def test_create_profile_invalid_name(self):
        """Test profile creation with invalid names."""
        invalid_names = [
            "",
            "test/user",  # path separator
            "test\\user",  # Windows path separator
            "../test",  # path traversal
            "test..user",  # contains ..
            "a" * 65,  # too long (>64 chars)
            "test@user",  # invalid character
            "test user",  # space not allowed
        ]
        
        for name in invalid_names:
            with self.assertRaises(ValueError):
                self.store.create_profile(
                    name=name,
                    voiceprint=self.sample_voiceprint,
                    metadata=self.sample_metadata
                )
    
    def test_create_profile_invalid_voiceprint_type(self):
        """Test profile creation with non-numpy array voiceprint."""
        with self.assertRaises(ValueError):
            self.store.create_profile(
                name="test_user",
                voiceprint=[0.1, 0.2, 0.3],  # list instead of numpy array
                metadata=self.sample_metadata
            )
    
    def test_create_profile_invalid_voiceprint_shape(self):
        """Test profile creation with wrong voiceprint dimension."""
        wrong_shape_voiceprint = np.random.randn(128).astype(np.float32)
        
        with self.assertRaises(ValueError):
            self.store.create_profile(
                name="test_user",
                voiceprint=wrong_shape_voiceprint,
                metadata=self.sample_metadata
            )
    
    def test_create_profile_already_exists(self):
        """Test profile creation when profile already exists."""
        # Create profile first time
        self.store.create_profile(
            name="test_user",
            voiceprint=self.sample_voiceprint,
            metadata=self.sample_metadata
        )
        
        # Try to create again
        with self.assertRaises(ValueError):
            self.store.create_profile(
                name="test_user",
                voiceprint=self.sample_voiceprint,
                metadata=self.sample_metadata
            )
    
    def test_profile_exists_true(self):
        """Test profile_exists returns True for existing profile."""
        self.store.create_profile(
            name="test_user",
            voiceprint=self.sample_voiceprint,
            metadata=self.sample_metadata
        )
        
        self.assertTrue(self.store.profile_exists("test_user"))
    
    def test_profile_exists_false(self):
        """Test profile_exists returns False for non-existent profile."""
        self.assertFalse(self.store.profile_exists("nonexistent_user"))
    
    def test_profile_exists_invalid_name(self):
        """Test profile_exists returns False for invalid names."""
        self.assertFalse(self.store.profile_exists("../test"))
        self.assertFalse(self.store.profile_exists(""))
    
    def test_get_profile_success(self):
        """Test successful profile retrieval."""
        self.store.create_profile(
            name="test_user",
            voiceprint=self.sample_voiceprint,
            metadata=self.sample_metadata
        )
        
        profile = self.store.get_profile("test_user")
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile['name'], "test_user")
        
        # Verify voiceprint
        np.testing.assert_array_almost_equal(
            profile['voiceprint'],
            self.sample_voiceprint,
            decimal=7
        )
        
        # Verify metadata
        self.assertEqual(profile['metadata']['sample_count'], 25)
        self.assertEqual(profile['metadata']['threshold'], 0.7)
        self.assertEqual(profile['metadata']['outliers_detected'], [3, 17])
    
    def test_get_profile_nonexistent(self):
        """Test get_profile returns None for non-existent profile."""
        profile = self.store.get_profile("nonexistent_user")
        self.assertIsNone(profile)
    
    def test_get_profile_invalid_name(self):
        """Test get_profile returns None for invalid names."""
        profile = self.store.get_profile("../test")
        self.assertIsNone(profile)
    
    def test_list_profiles_empty(self):
        """Test list_profiles returns empty list when no profiles exist."""
        profiles = self.store.list_profiles()
        self.assertEqual(profiles, [])
    
    def test_list_profiles_multiple(self):
        """Test list_profiles returns all profiles."""
        # Create multiple profiles
        for i in range(3):
            voiceprint = np.random.randn(192).astype(np.float32)
            voiceprint = voiceprint / np.linalg.norm(voiceprint)
            
            metadata = self.sample_metadata.copy()
            metadata['sample_count'] = 10 + i
            
            self.store.create_profile(
                name=f"user_{i}",
                voiceprint=voiceprint,
                metadata=metadata
            )
        
        profiles = self.store.list_profiles()
        
        self.assertEqual(len(profiles), 3)
        
        # Check names
        names = {p['name'] for p in profiles}
        self.assertEqual(names, {"user_0", "user_1", "user_2"})
        
        # Check metadata is included
        for profile in profiles:
            self.assertIn('metadata', profile)
            self.assertIn('sample_count', profile['metadata'])
    
    def test_delete_profile_success(self):
        """Test successful profile deletion."""
        self.store.create_profile(
            name="test_user",
            voiceprint=self.sample_voiceprint,
            metadata=self.sample_metadata
        )
        
        self.assertTrue(self.store.profile_exists("test_user"))
        
        result = self.store.delete_profile("test_user")
        
        self.assertTrue(result)
        self.assertFalse(self.store.profile_exists("test_user"))
        
        # Verify directory no longer exists
        profile_dir = Path(self.test_dir) / "test_user"
        self.assertFalse(profile_dir.exists())
    
    def test_delete_profile_nonexistent(self):
        """Test delete_profile returns False for non-existent profile."""
        result = self.store.delete_profile("nonexistent_user")
        self.assertFalse(result)
    
    def test_delete_profile_invalid_name(self):
        """Test delete_profile returns False for invalid names."""
        result = self.store.delete_profile("../test")
        self.assertFalse(result)
    
    def test_update_threshold_success(self):
        """Test successful threshold update."""
        self.store.create_profile(
            name="test_user",
            voiceprint=self.sample_voiceprint,
            metadata=self.sample_metadata
        )
        
        result = self.store.update_threshold("test_user", 0.85)
        
        self.assertTrue(result)
        
        # Verify threshold updated
        profile = self.store.get_profile("test_user")
        self.assertEqual(profile['metadata']['threshold'], 0.85)
        
        # Verify other metadata unchanged
        self.assertEqual(profile['metadata']['sample_count'], 25)
        self.assertEqual(profile['metadata']['outliers_detected'], [3, 17])
    
    def test_update_threshold_nonexistent(self):
        """Test update_threshold returns False for non-existent profile."""
        result = self.store.update_threshold("nonexistent_user", 0.85)
        self.assertFalse(result)
    
    def test_update_threshold_invalid_range(self):
        """Test update_threshold raises ValueError for out-of-range threshold."""
        self.store.create_profile(
            name="test_user",
            voiceprint=self.sample_voiceprint,
            metadata=self.sample_metadata
        )
        
        # Test below range
        with self.assertRaises(ValueError):
            self.store.update_threshold("test_user", -0.1)
        
        # Test above range
        with self.assertRaises(ValueError):
            self.store.update_threshold("test_user", 1.1)
    
    def test_update_threshold_boundary_values(self):
        """Test update_threshold accepts boundary values 0.0 and 1.0."""
        self.store.create_profile(
            name="test_user",
            voiceprint=self.sample_voiceprint,
            metadata=self.sample_metadata
        )
        
        # Test 0.0
        result = self.store.update_threshold("test_user", 0.0)
        self.assertTrue(result)
        profile = self.store.get_profile("test_user")
        self.assertEqual(profile['metadata']['threshold'], 0.0)
        
        # Test 1.0
        result = self.store.update_threshold("test_user", 1.0)
        self.assertTrue(result)
        profile = self.store.get_profile("test_user")
        self.assertEqual(profile['metadata']['threshold'], 1.0)
    
    def test_voiceprint_persistence_round_trip(self):
        """Test voiceprint survives save/load cycle with high precision."""
        self.store.create_profile(
            name="test_user",
            voiceprint=self.sample_voiceprint,
            metadata=self.sample_metadata
        )
        
        profile = self.store.get_profile("test_user")
        loaded_voiceprint = profile['voiceprint']
        
        # Test element-wise equality with tight tolerance
        np.testing.assert_array_almost_equal(
            loaded_voiceprint,
            self.sample_voiceprint,
            decimal=7
        )
        
        # Test shape preserved
        self.assertEqual(loaded_voiceprint.shape, (192,))
    
    def test_metadata_json_round_trip(self):
        """Test metadata survives JSON serialize/deserialize cycle."""
        self.store.create_profile(
            name="test_user",
            voiceprint=self.sample_voiceprint,
            metadata=self.sample_metadata
        )
        
        profile = self.store.get_profile("test_user")
        loaded_metadata = profile['metadata']
        
        # Test all fields preserved
        self.assertEqual(loaded_metadata['sample_count'], 
                        self.sample_metadata['sample_count'])
        self.assertEqual(loaded_metadata['threshold'], 
                        self.sample_metadata['threshold'])
        self.assertEqual(loaded_metadata['outliers_detected'], 
                        self.sample_metadata['outliers_detected'])
        self.assertEqual(loaded_metadata['intra_class_stats'], 
                        self.sample_metadata['intra_class_stats'])
        self.assertEqual(loaded_metadata['version'], 
                        self.sample_metadata['version'])
    
    def test_valid_profile_names(self):
        """Test various valid profile name patterns."""
        valid_names = [
            "user1",
            "john_doe",
            "alice-bob",
            "user_123",
            "a",  # single character
            "a" * 64,  # maximum length
            "User_Name-123",  # mixed case, underscore, hyphen, numbers
        ]
        
        for name in valid_names:
            voiceprint = np.random.randn(192).astype(np.float32)
            voiceprint = voiceprint / np.linalg.norm(voiceprint)
            
            result = self.store.create_profile(
                name=name,
                voiceprint=voiceprint,
                metadata=self.sample_metadata.copy()
            )
            
            self.assertTrue(result, f"Failed to create profile with valid name: {name}")
            self.assertTrue(self.store.profile_exists(name))
            
            # Clean up
            self.store.delete_profile(name)
    
    def test_atomic_write_voiceprint(self):
        """Test that voiceprint write is atomic (no .tmp files left behind)."""
        self.store.create_profile(
            name="test_user",
            voiceprint=self.sample_voiceprint,
            metadata=self.sample_metadata
        )
        
        profile_dir = Path(self.test_dir) / "test_user"
        
        # Check no temporary files exist
        tmp_files = list(profile_dir.glob("*.tmp"))
        self.assertEqual(len(tmp_files), 0)
    
    def test_atomic_write_metadata(self):
        """Test that metadata write is atomic (no .tmp files left behind)."""
        self.store.create_profile(
            name="test_user",
            voiceprint=self.sample_voiceprint,
            metadata=self.sample_metadata
        )
        
        profile_dir = Path(self.test_dir) / "test_user"
        
        # Check no temporary files exist
        tmp_files = list(profile_dir.glob("*.tmp"))
        self.assertEqual(len(tmp_files), 0)


if __name__ == '__main__':
    unittest.main()
