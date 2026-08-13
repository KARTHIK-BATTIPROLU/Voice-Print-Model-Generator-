"""
File-based voice profile storage and retrieval.

Storage layout:
    profiles/
        <name>/
            voiceprint.npy   — averaged L2-normalized embedding (float32)
            meta.json        — name, sample_count, created_at, threshold, stats
"""
import os
import json
import logging
import numpy as np
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Base directory — resolved relative to THIS file so it works regardless of cwd
_BASE = os.path.join(os.path.dirname(__file__), "profiles")


# ─── helpers ─────────────────────────────────────────────────────────────────

def _profile_dir(name: str) -> str:
    safe = name.replace("/", "_").replace("..", "_").strip()
    return os.path.join(_BASE, safe)

def _voiceprint_path(name: str) -> str:
    return os.path.join(_profile_dir(name), "voiceprint.npy")

def _meta_path(name: str) -> str:
    return os.path.join(_profile_dir(name), "meta.json")


# ─── Public API ──────────────────────────────────────────────────────────────

def save_profile(
    name: str,
    voiceprint: np.ndarray,
    sample_count: int,
    threshold: float = 0.70,
    intra_class_stats: Optional[dict] = None,
) -> dict:
    """
    Persist a speaker voiceprint + metadata to disk.

    Args:
        name             : speaker name (used as directory key)
        voiceprint       : L2-normalized mean embedding (float32 ndarray)
        sample_count     : number of enrollment samples used
        threshold        : verification threshold
        intra_class_stats: pairwise similarity stats dict

    Returns:
        metadata dict saved to disk
    """
    os.makedirs(_profile_dir(name), exist_ok=True)

    np.save(_voiceprint_path(name), voiceprint.astype(np.float32))

    meta = {
        "name":               name,
        "sample_count":       sample_count,
        "created_at":         datetime.now(timezone.utc).isoformat(),
        "threshold":          threshold,
        "intra_class_stats":  intra_class_stats or {},
    }
    with open(_meta_path(name), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"Profile saved: '{name}' ({sample_count} samples)")
    return meta


def load_profile(name: str) -> Optional[dict]:
    """
    Load a profile's metadata + voiceprint from disk.

    Returns:
        dict with keys: name, sample_count, created_at, threshold,
                        intra_class_stats, voiceprint (np.ndarray)
        or None if profile doesn't exist.
    """
    if not profile_exists(name):
        return None

    meta_file = _meta_path(name)
    vp_file   = _voiceprint_path(name)

    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    meta["voiceprint"] = np.load(vp_file).astype(np.float32)
    return meta


def profile_exists(name: str) -> bool:
    """Check whether a profile exists on disk."""
    return (os.path.isfile(_meta_path(name)) and
            os.path.isfile(_voiceprint_path(name)))


def list_profiles() -> list[dict]:
    """
    Return metadata for all stored profiles (no voiceprint arrays).
    """
    if not os.path.isdir(_BASE):
        return []

    profiles = []
    for entry in sorted(os.listdir(_BASE)):
        meta_file = os.path.join(_BASE, entry, "meta.json")
        if os.path.isfile(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                profiles.append(meta)
            except Exception as e:
                logger.warning(f"Could not read profile '{entry}': {e}")

    return profiles


def delete_profile(name: str) -> bool:
    """
    Delete a speaker profile from disk.

    Returns:
        True if deleted, False if not found.
    """
    pdir = _profile_dir(name)
    if not os.path.isdir(pdir):
        return False

    for fname in os.listdir(pdir):
        os.remove(os.path.join(pdir, fname))
    os.rmdir(pdir)
    logger.info(f"Profile deleted: '{name}'")
    return True


def update_threshold(name: str, threshold: float) -> Optional[dict]:
    """
    Update only the threshold field of an existing profile's metadata.

    Returns updated metadata dict, or None if profile not found.
    """
    if not profile_exists(name):
        return None

    with open(_meta_path(name), "r", encoding="utf-8") as f:
        meta = json.load(f)

    meta["threshold"] = round(float(threshold), 4)

    with open(_meta_path(name), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return meta


def count_profiles() -> int:
    """Return total number of stored profiles."""
    return len(list_profiles())
