"""
Utility functions for Voice Print Model Generator
"""
import os
import numpy as np


def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def list_audio_files(directory: str, extensions=(".wav", ".flac", ".mp3")) -> list:
    """Recursively list all audio files in a directory."""
    audio_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(extensions):
                audio_files.append(os.path.join(root, file))
    return sorted(audio_files)


def get_speaker_label(filepath: str) -> str:
    """
    Extract speaker label from file path.
    Assumes structure: data/samples/<speaker_name>/audio.wav
    """
    return os.path.basename(os.path.dirname(filepath))


def normalize_features(features: np.ndarray) -> np.ndarray:
    """Normalize feature array to zero mean and unit variance."""
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0) + 1e-8
    return (features - mean) / std


def print_banner():
    """Print project banner."""
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("=" * 55)
    print("   🎙️  Voice Print Model Generator")
    print("   Speaker Recognition using MFCC + GMM")
    print("=" * 55)

