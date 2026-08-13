"""
Voice Print Model — GMM-based speaker recognition model.
Each speaker is represented by a Gaussian Mixture Model (GMM)
trained on their MFCC feature vectors.
"""
import os
import numpy as np
import joblib
from sklearn.mixture import GaussianMixture
from typing import Dict, Optional, Tuple


class VoicePrintModel:
    """
    Speaker recognition model using per-speaker GMMs.
    """

    def __init__(self, n_components: int = 16, covariance_type: str = "diag"):
        """
        Args:
            n_components:    Number of Gaussian components per speaker GMM.
            covariance_type: GMM covariance type ('full', 'diag', 'tied', 'spherical').
        """
        self.n_components = n_components
        self.covariance_type = covariance_type
        self.speaker_models: Dict[str, GaussianMixture] = {}
        self.speaker_labels: list = []

    def train_speaker(self, speaker_id: str, features: np.ndarray) -> None:
        """
        Train a GMM for a single speaker.

        Args:
            speaker_id: Unique speaker identifier string.
            features:   Feature matrix of shape (n_frames, n_features).
        """
        print(f"  Training GMM for speaker: '{speaker_id}' "
              f"({features.shape[0]} frames, {features.shape[1]} features)")

        gmm = GaussianMixture(
            n_components=min(self.n_components, features.shape[0] // 2),
            covariance_type=self.covariance_type,
            max_iter=200,
            random_state=42,
        )
        gmm.fit(features)
        self.speaker_models[speaker_id] = gmm

        if speaker_id not in self.speaker_labels:
            self.speaker_labels.append(speaker_id)

        print(f"  ✓ Speaker '{speaker_id}' model trained "
              f"(converged: {gmm.converged_})")

    def score(self, speaker_id: str, features: np.ndarray) -> float:
        """
        Compute average log-likelihood of features under a speaker's GMM.

        Args:
            speaker_id: Speaker to score against.
            features:   Feature matrix of shape (n_frames, n_features).

        Returns:
            Average log-likelihood score (higher = more likely this speaker).
        """
        if speaker_id not in self.speaker_models:
            raise ValueError(f"Unknown speaker: '{speaker_id}'")
        return self.speaker_models[speaker_id].score(features)

    def predict(self, features: np.ndarray) -> Tuple[str, Dict[str, float]]:
        """
        Identify the most likely speaker for given features.

        Args:
            features: Feature matrix of shape (n_frames, n_features).

        Returns:
            (predicted_speaker, {speaker_id: score, ...})
        """
        if not self.speaker_models:
            raise RuntimeError("No speaker models trained yet.")

        scores = {
            spk: self.score(spk, features)
            for spk in self.speaker_labels
        }
        predicted = max(scores, key=scores.get)
        return predicted, scores

    def save(self, model_path: str) -> None:
        """Save the trained model to disk."""
        os.makedirs(os.path.dirname(model_path) or ".", exist_ok=True)
        payload = {
            "n_components": self.n_components,
            "covariance_type": self.covariance_type,
            "speaker_models": self.speaker_models,
            "speaker_labels": self.speaker_labels,
        }
        joblib.dump(payload, model_path)
        print(f"✓ Model saved → {model_path}")

    @classmethod
    def load(cls, model_path: str) -> "VoicePrintModel":
        """Load a trained model from disk."""
        payload = joblib.load(model_path)
        model = cls(
            n_components=payload["n_components"],
            covariance_type=payload["covariance_type"],
        )
        model.speaker_models = payload["speaker_models"]
        model.speaker_labels = payload["speaker_labels"]
        print(f"✓ Model loaded ← {model_path} "
              f"({len(model.speaker_labels)} speakers)")
        return model

    @property
    def num_speakers(self) -> int:
        return len(self.speaker_labels)

    def __repr__(self) -> str:
        return (
            f"VoicePrintModel(speakers={self.num_speakers}, "
            f"n_components={self.n_components}, "
            f"covariance={self.covariance_type})"
        )
