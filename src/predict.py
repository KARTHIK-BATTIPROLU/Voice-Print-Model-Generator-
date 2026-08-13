"""
Prediction / Inference module for Voice Print Model Generator.
"""
import numpy as np
from src.feature_extractor import FeatureExtractor
from src.model import VoicePrintModel
from src.utils import normalize_features


def predict_speaker(
    audio_path: str,
    model: VoicePrintModel,
    normalize: bool = True,
) -> dict:
    """
    Predict the speaker of a given audio file.

    Args:
        audio_path: Path to .wav audio file.
        model:      Trained VoicePrintModel.
        normalize:  Whether to normalize features before scoring.

    Returns:
        dict with keys: predicted_speaker, scores, confidence
    """
    extractor = FeatureExtractor()
    features = extractor.extract_from_file(audio_path)

    if normalize:
        features = normalize_features(features)

    predicted, scores = model.predict(features)

    # Compute confidence as softmax-like ratio
    score_values = list(scores.values())
    max_score = max(score_values)
    # Simple relative confidence
    confidence = 1.0
    if len(score_values) > 1:
        sorted_scores = sorted(score_values, reverse=True)
        gap = sorted_scores[0] - sorted_scores[1]
        confidence = min(1.0, max(0.0, (gap + 10) / 20))

    return {
        "predicted_speaker": predicted,
        "scores": scores,
        "confidence": round(confidence, 4),
    }


def predict_from_array(
    audio: np.ndarray,
    model: VoicePrintModel,
    sample_rate: int = 16000,
    normalize: bool = True,
) -> dict:
    """
    Predict the speaker from a raw audio numpy array.

    Args:
        audio:       Raw audio samples as float32 numpy array.
        model:       Trained VoicePrintModel.
        sample_rate: Sample rate of the audio.
        normalize:   Whether to normalize features.

    Returns:
        dict with keys: predicted_speaker, scores, confidence
    """
    extractor = FeatureExtractor(sample_rate=sample_rate)
    features = extractor.extract_from_array(audio)

    if normalize:
        features = normalize_features(features)

    predicted, scores = model.predict(features)

    score_values = list(scores.values())
    confidence = 1.0
    if len(score_values) > 1:
        sorted_scores = sorted(score_values, reverse=True)
        gap = sorted_scores[0] - sorted_scores[1]
        confidence = min(1.0, max(0.0, (gap + 10) / 20))

    return {
        "predicted_speaker": predicted,
        "scores": scores,
        "confidence": round(confidence, 4),
    }
