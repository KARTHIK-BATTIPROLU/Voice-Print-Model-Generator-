import os
from typing import List
from dataclasses import dataclass, field
try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class EnrollmentConfig:
    """Enrollment-specific configuration"""
    min_samples: int = 10
    max_samples: int = 500
    outlier_threshold: float = 2.5
    target_samples: int = 20
    holdout_samples: int = 2
    single_session_lock: bool = True
    speaker_id: str = "ASTA_primary"
    min_rms_db: float = -35.0
    max_clip_peak: float = 0.98


@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = field(default_factory=lambda: [
        o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()
    ])


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


def _load_yaml_config(app_config: AppConfig) -> AppConfig:
    """Loads config.yaml if available and overrides defaults."""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "config.yaml"),
        os.path.join(os.path.dirname(__file__), "config.yaml"),
        "config.yaml"
    ]
    if not yaml:
        return app_config

    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data and "enrollment" in data:
                    enr_data = data["enrollment"]
                    for key, val in enr_data.items():
                        if hasattr(app_config.enrollment, key):
                            setattr(app_config.enrollment, key, val)
                break
            except Exception as e:
                print(f"Warning: Failed to parse {path}: {e}")
    return app_config


# Global configuration instance
config = _load_yaml_config(AppConfig())

