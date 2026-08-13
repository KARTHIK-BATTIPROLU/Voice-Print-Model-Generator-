"""
Feature Extractor — extracts MFCC and other audio features
for speaker recognition / voice print generation.
"""
import numpy as np

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("[WARNING] librosa not installed. Using synthetic features for demo.")


class FeatureExtractor:
    """
    Extracts MFCC-based voice print features from audio files.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        n_mfcc: int = 40,
        n_fft: int = 512,
        hop_length: int = 160,
        n_mels: int = 40,
    ):
        self.sample_rate = sample_rate
        self.n_mfcc = n_mfcc
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels

    def load_audio(self, filepath: str) -> np.ndarray:
        """Load audio file and resample to target sample rate."""
        if not LIBROSA_AVAILABLE:
            # Return synthetic audio for demo
            duration = 3  # seconds
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            return np.sin(2 * np.pi * 440 * t) + 0.1 * np.random.randn(len(t))

        audio, _ = librosa.load(filepath, sr=self.sample_rate, mono=True)
        return audio

    def extract_mfcc(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract MFCC features from audio signal.
        Returns array of shape (n_frames, n_mfcc).
        """
        if not LIBROSA_AVAILABLE:
            # Return synthetic MFCC features for demo
            n_frames = max(1, len(audio) // self.hop_length)
            return np.random.randn(n_frames, self.n_mfcc).astype(np.float32)

        mfcc = librosa.feature.mfcc(
            y=audio,
            sr=self.sample_rate,
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            n_mels=self.n_mels,
        )
        # Delta features (velocity)
        delta = librosa.feature.delta(mfcc)
        # Delta-delta features (acceleration)
        delta2 = librosa.feature.delta(mfcc, order=2)

        # Concatenate: shape (3*n_mfcc, n_frames) → transpose → (n_frames, 3*n_mfcc)
        features = np.concatenate([mfcc, delta, delta2], axis=0).T
        return features.astype(np.float32)

    def extract_from_file(self, filepath: str) -> np.ndarray:
        """Load audio file and extract MFCC features."""
        audio = self.load_audio(filepath)
        return self.extract_mfcc(audio)

    def extract_from_array(self, audio: np.ndarray) -> np.ndarray:
        """Extract MFCC features from a raw audio array."""
        return self.extract_mfcc(audio)

    @property
    def feature_dim(self) -> int:
        """Dimensionality of extracted feature vectors."""
        if LIBROSA_AVAILABLE:
            return self.n_mfcc * 3  # MFCC + delta + delta2
        return self.n_mfcc
