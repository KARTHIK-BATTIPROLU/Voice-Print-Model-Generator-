"""
Training pipeline for Voice Print Model Generator.
Loads audio samples, extracts features, and trains per-speaker GMMs.
"""
import os
import numpy as np
from collections import defaultdict

from src.feature_extractor import FeatureExtractor
from src.model import VoicePrintModel
from src.utils import list_audio_files, get_speaker_label, normalize_features


def train(
    data_dir: str,
    model_save_path: str = "models/voice_print_model.pkl",
    n_components: int = 16,
    normalize: bool = True,
) -> VoicePrintModel:
    """
    Full training pipeline.

    Args:
        data_dir:         Path to directory containing speaker subdirectories.
        model_save_path:  Where to save the trained model.
        n_components:     Number of GMM components per speaker.
        normalize:        Whether to normalize features.

    Returns:
        Trained VoicePrintModel.

    Directory structure expected:
        data_dir/
            speaker_1/
                audio1.wav
                audio2.wav
            speaker_2/
                audio1.wav
            ...
    """
    print(f"\n[Training] Scanning audio files in: {data_dir}")
    audio_files = list_audio_files(data_dir)

    if not audio_files:
        raise FileNotFoundError(
            f"No audio files found in '{data_dir}'. "
            "Please add .wav/.flac/.mp3 files under speaker subdirectories."
        )

    print(f"[Training] Found {len(audio_files)} audio file(s).")

    # Group files by speaker label
    speaker_files = defaultdict(list)
    for filepath in audio_files:
        label = get_speaker_label(filepath)
        speaker_files[label].append(filepath)

    print(f"[Training] Speakers detected: {list(speaker_files.keys())}\n")

    extractor = FeatureExtractor()
    model = VoicePrintModel(n_components=n_components)

    for speaker, files in speaker_files.items():
        all_features = []
        for filepath in files:
            try:
                features = extractor.extract_from_file(filepath)
                all_features.append(features)
            except Exception as e:
                print(f"  [WARNING] Could not process {filepath}: {e}")

        if not all_features:
            print(f"  [SKIP] No valid features for speaker '{speaker}'")
            continue

        combined = np.vstack(all_features)
        if normalize:
            combined = normalize_features(combined)

        model.train_speaker(speaker, combined)

    model.save(model_save_path)
    print(f"\n[Training] Complete! {model.num_speakers} speaker(s) trained.")
    return model
