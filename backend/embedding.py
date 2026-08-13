"""
Embedding extraction and similarity computation engine.
Uses SpeechBrain ECAPA-TDNN to extract 192-dim speaker embeddings.
Falls back to MFCC-based embeddings if SpeechBrain model unavailable.
"""
import numpy as np
import torch
import torchaudio
import logging

logger = logging.getLogger(__name__)

# ─── ECAPA-TDNN via SpeechBrain ──────────────────────────────────────────────
_encoder = None
_encoder_failed = False   # if model download fails, use MFCC fallback

def _get_encoder():
    global _encoder, _encoder_failed
    if _encoder is not None:
        return _encoder
    if _encoder_failed:
        return None
    try:
        from speechbrain.pretrained import EncoderClassifier
        logger.info("Loading SpeechBrain ECAPA-TDNN...")
        _encoder = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="pretrained_models/spkrec-ecapa-voxceleb",
            run_opts={"device": "cpu"},
        )
        logger.info("ECAPA-TDNN loaded OK")
        return _encoder
    except Exception as e:
        logger.warning(f"SpeechBrain load failed ({e}), using MFCC fallback")
        _encoder_failed = True
        return None


# ─── MFCC-based fallback embedding (no heavy deps) ───────────────────────────
def _mfcc_embedding(waveform: torch.Tensor, sr: int = 16000, n_mfcc: int = 40) -> np.ndarray:
    """
    Compute a deterministic embedding from a waveform using
    torchaudio MFCC + delta + delta2 statistics (mean + std per coefficient).
    Consistent across identical audio — produces stable cosine similarity.
    n_mfcc=40, n_mels=80  →  feature dim = 3*40*2 = 240, padded/truncated to 256.
    """
    if waveform.dim() == 2:
        waveform = waveform.mean(dim=0, keepdim=True)

    n_mels = max(n_mfcc * 2, 80)   # always n_mels > n_mfcc
    mfcc_transform = torchaudio.transforms.MFCC(
        sample_rate=sr,
        n_mfcc=n_mfcc,
        melkwargs={"n_fft": 512, "hop_length": 160, "n_mels": n_mels},
    )
    mfcc = mfcc_transform(waveform)          # (1, n_mfcc, T)

    # delta features
    delta  = torchaudio.functional.compute_deltas(mfcc)
    delta2 = torchaudio.functional.compute_deltas(delta)

    feats = torch.cat([mfcc, delta, delta2], dim=1)  # (1, 3*n_mfcc, T)

    mean = feats.mean(dim=-1).squeeze(0)   # (3*n_mfcc,)
    std  = feats.std(dim=-1).squeeze(0)    # (3*n_mfcc,)

    emb = torch.cat([mean, std], dim=0).numpy()   # (6*n_mfcc,) = 768-dim
    # truncate/pad to exactly 256 for speed
    emb = emb[:256] if len(emb) >= 256 else np.pad(emb, (0, 256 - len(emb)))
    return emb.astype(np.float32)


# ─── Public API ──────────────────────────────────────────────────────────────

def extract_embedding(waveform: torch.Tensor, sr: int = 16000) -> np.ndarray:
    """
    Extract a speaker embedding from a waveform tensor.
    Tries ECAPA-TDNN first; falls back to MFCC stats if unavailable.

    Args:
        waveform : torch.Tensor [1, samples] at target_sr (16 kHz)
        sr       : sample rate (should always be 16000)

    Returns:
        np.ndarray shape (D,) — unnormalized embedding
    """
    encoder = _get_encoder()
    if encoder is not None:
        try:
            with torch.no_grad():
                emb = encoder.encode_batch(waveform)   # (1, 1, D)
            return emb.squeeze().numpy().astype(np.float32)
        except Exception as e:
            logger.warning(f"ECAPA inference failed ({e}), using MFCC fallback")

    return _mfcc_embedding(waveform, sr)


def normalize_embedding(emb: np.ndarray) -> np.ndarray:
    """L2-normalize an embedding vector."""
    norm = np.linalg.norm(emb)
    if norm < 1e-9:
        return emb
    return emb / norm


def average_embeddings(embeddings: list[np.ndarray]) -> np.ndarray:
    """
    Average a list of L2-normalized embeddings and re-normalize.
    Used to create a single voiceprint from multiple enrollment samples.
    """
    stacked = np.stack(embeddings, axis=0)          # (N, D)
    mean_emb = stacked.mean(axis=0)                  # (D,)
    return normalize_embedding(mean_emb)


def compute_cosine_similarity(emb_a: np.ndarray, emb_b: np.ndarray) -> float:
    """
    Cosine similarity between two embeddings. Both should be L2-normalized.
    Returns float in [-1.0, 1.0]. Identical vectors → 1.0.
    """
    a = normalize_embedding(emb_a)
    b = normalize_embedding(emb_b)
    score = float(np.dot(a, b))
    return max(-1.0, min(1.0, score))          # clamp for floating-point safety


def detect_outliers(embeddings: list[np.ndarray], threshold: float = 2.5) -> list[bool]:
    """
    Detect outlier embeddings via z-score of pairwise cosine distances.

    Args:
        embeddings : list of L2-normalized embeddings
        threshold  : z-score threshold (default 2.5σ)

    Returns:
        list[bool] — True = keep, False = outlier
    """
    n = len(embeddings)
    if n <= 2:
        return [True] * n

    # mean pairwise cosine similarity for each embedding vs. others
    scores = []
    for i in range(n):
        sims = [compute_cosine_similarity(embeddings[i], embeddings[j])
                for j in range(n) if j != i]
        scores.append(np.mean(sims))

    scores_arr = np.array(scores)
    mean_s = scores_arr.mean()
    std_s  = scores_arr.std() + 1e-9
    z      = (scores_arr - mean_s) / std_s
    return [bool(z_i > -threshold) for z_i in z]


def compute_intra_class_stats(embeddings: list[np.ndarray]) -> dict:
    """
    Compute pairwise cosine similarity statistics within a set of embeddings.
    Used to suggest a verification threshold for a new profile.
    """
    n = len(embeddings)
    if n < 2:
        return {"mean_similarity": 1.0, "std_similarity": 0.0,
                "min_similarity": 1.0, "suggested_threshold": 0.75}

    sims = []
    for i in range(n):
        for j in range(i + 1, n):
            sims.append(compute_cosine_similarity(embeddings[i], embeddings[j]))

    sims_arr = np.array(sims)
    mean_sim = float(sims_arr.mean())
    std_sim  = float(sims_arr.std())
    # conservative threshold: mean - 1.5*std, floored at 0.50, capped at 0.92
    # Cap at 0.92 because identical audio still scores < 1.0 due to float ops
    suggested = min(0.92, max(0.50, round(mean_sim - 1.5 * std_sim, 3)))

    return {
        "mean_similarity": round(mean_sim, 4),
        "std_similarity":  round(std_sim,  4),
        "min_similarity":  round(float(sims_arr.min()), 4),
        "suggested_threshold": suggested,
    }
