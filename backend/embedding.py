"""
Embedding extraction and similarity computation engine.
Validates: Requirements 1, 2, 9
"""
import numpy as np
import torch
from model import ModelLoader


def extract_embedding(waveform: torch.Tensor, sample_rate: int) -> np.ndarray:
    """
    Extract ECAPA-TDNN embedding from audio waveform.
    
    Args:
        waveform: Audio waveform tensor (1D or 2D with shape [channels, samples])
        sample_rate: Sample rate of the waveform (Hz)
    
    Returns:
        192-dimensional embedding vector as numpy array
        
    Validates: Requirements 1.6, 2.5
    """
    # Get singleton model instance
    model = ModelLoader.get_instance()
    
    # Ensure waveform is 2D: [batch, samples]
    if waveform.dim() == 1:
        waveform = waveform.unsqueeze(0)
    elif waveform.dim() == 2 and waveform.shape[0] > 1:
        # If multi-channel, take first channel
        waveform = waveform[0:1, :]
    
    # Extract embedding using SpeechBrain model
    # Model expects waveform tensor and returns embedding tensor
    with torch.no_grad():
        embedding = model.encode_batch(waveform)
    
    # Convert to numpy array and squeeze to 1D
    embedding_np = embedding.squeeze().cpu().numpy()
    
    return embedding_np


def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    """
    Apply L2 normalization to embedding vector.
    
    Args:
        embedding: Embedding vector to normalize
    
    Returns:
        L2-normalized embedding (unit vector with L2 norm = 1.0)
        
    Validates: Requirements 1.7, 2.6
    """
    # Compute L2 norm
    norm = np.linalg.norm(embedding)
    
    # Avoid division by zero
    if norm < 1e-12:
        return embedding
    
    # Normalize to unit vector
    normalized = embedding / norm
    
    return normalized


def average_embeddings(embeddings: list[np.ndarray]) -> np.ndarray:
    """
    Compute element-wise mean of embedding vectors.
    
    Args:
        embeddings: List of embedding vectors to average
    
    Returns:
        Averaged embedding vector (element-wise mean)
        
    Validates: Requirements 1.8
    """
    if not embeddings:
        raise ValueError("Cannot average empty list of embeddings")
    
    # Stack embeddings and compute mean along axis 0
    embeddings_array = np.stack(embeddings, axis=0)
    averaged = np.mean(embeddings_array, axis=0)
    
    return averaged


def compute_cosine_similarity(embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two L2-normalized embeddings.
    
    For L2-normalized vectors (unit vectors), cosine similarity equals the dot product.
    
    Args:
        embedding_a: First embedding vector (L2-normalized, shape: (192,))
        embedding_b: Second embedding vector (L2-normalized, shape: (192,))
    
    Returns:
        Cosine similarity score in range [-1, 1]
    
    Validates: Requirements 1.9, 2.7, 3.2, 9.3
    """
    # For L2-normalized vectors, cosine similarity is simply the dot product
    similarity = float(np.dot(embedding_a, embedding_b))
    return similarity


def detect_outliers(embeddings: list[np.ndarray], threshold: float = 2.5) -> list[int]:
    """
    Detect outlier embeddings using z-score method on pairwise similarities.
    
    An embedding is considered an outlier if its mean similarity to all other
    embeddings has a z-score exceeding the threshold (default: 2.5 std deviations).
    
    Args:
        embeddings: List of L2-normalized embedding vectors
        threshold: Z-score threshold for outlier detection (default: 2.5)
    
    Returns:
        List of indices for embeddings identified as outliers
    
    Validates: Requirements 1.10
    """
    if len(embeddings) < 2:
        return []
    
    n = len(embeddings)
    
    # Compute mean similarity for each embedding to all others
    mean_similarities = []
    for i in range(n):
        similarities = []
        for j in range(n):
            if i != j:
                sim = compute_cosine_similarity(embeddings[i], embeddings[j])
                similarities.append(sim)
        mean_similarities.append(np.mean(similarities))
    
    mean_similarities = np.array(mean_similarities)
    
    # Compute z-scores
    overall_mean = np.mean(mean_similarities)
    overall_std = np.std(mean_similarities)
    
    # Avoid division by zero if all similarities are identical
    if overall_std == 0:
        return []
    
    z_scores = (mean_similarities - overall_mean) / overall_std
    
    # Find outliers (embeddings with z-score below -threshold)
    # Low similarity = outlier (different from the group)
    outlier_indices = [i for i, z in enumerate(z_scores) if z < -threshold]
    
    return outlier_indices


def compute_intra_class_stats(embeddings: list[np.ndarray]) -> dict:
    """
    Compute statistics for enrollment sample cohesion.
    
    Calculates pairwise cosine similarities between all embeddings and returns
    statistical measures (mean, std, min, max) to assess sample quality and consistency.
    
    Args:
        embeddings: List of L2-normalized embedding vectors
    
    Returns:
        Dictionary containing:
        - mean_similarity: Mean of all pairwise similarities
        - std_similarity: Standard deviation of pairwise similarities
        - min_similarity: Minimum pairwise similarity
        - max_similarity: Maximum pairwise similarity
    
    Validates: Requirements 1.9
    """
    if len(embeddings) < 2:
        return {
            "mean_similarity": 1.0,
            "std_similarity": 0.0,
            "min_similarity": 1.0,
            "max_similarity": 1.0
        }
    
    # Compute all pairwise similarities
    n = len(embeddings)
    similarities = []
    
    for i in range(n):
        for j in range(i + 1, n):
            sim = compute_cosine_similarity(embeddings[i], embeddings[j])
            similarities.append(sim)
    
    similarities = np.array(similarities)
    
    return {
        "mean_similarity": float(np.mean(similarities)),
        "std_similarity": float(np.std(similarities)),
        "min_similarity": float(np.min(similarities)),
        "max_similarity": float(np.max(similarities))
    }
