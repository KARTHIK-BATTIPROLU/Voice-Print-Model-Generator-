"""
Application configuration for VoicePrint system.
Validates: Requirements 8.2, 11.3
"""
from typing import List
from dataclasses import dataclass, field


@dataclass
class EnrollmentConfig:
    """Enrollment-specific configuration"""
    min_samples: int = 10
    max_samples: int = 500
    outlier_threshold: float = 2.5


@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:5173"])


@dataclass
class AppConfig:
    """Main application configuration"""
    model_path: str = "speechbrain/spkrec-ecapa-voxceleb"
    storage_path: str = "profiles"
    default_threshold: float = 0.7
    target_sample_rate: int = 16000
    min_snr_db: float = 5.0
    min_duration_sec: float = 1.5
    max_file_size_mb: int = 50
    enrollment: EnrollmentConfig = field(default_factory=EnrollmentConfig)
    server: ServerConfig = field(default_factory=ServerConfig)


# Global configuration instance
config = AppConfig()
