"""
Unit tests for embedding extraction and processing.
Validates: Requirements 1.6, 1.7, 1.8, 2.5, 2.6
"""
import pytest
import numpy as np
import torch
from embedding import extract_embedding, normalize_embedding, average_embeddings


class TestExtractEmbedding:
    """Test embedding extraction functionality"""
    
    def test_extract_embedding_produces_192_dimensions(self):
        """Validate that embedding extraction produces 192-dimensional vectors"""
        # Create a dummy audio waveform (1.5 seconds at 16kHz)
        duration = 1.5
        sample_rate = 16000
        num_samples = int(duration * sample_rate)
        waveform = torch.randn(num_samples)
        
        # Extract embedding
        embedding = extract_embedding(waveform, sample_rate)
        
        # Verify shape
        assert isinstance(embedding, np.ndarray), "Embedding should be numpy array"
        assert embedding.shape == (192,), f"Expected shape (192,), got {embedding.shape}"
    
    def test_extract_embedding_handles_2d_waveform(self):
        """Verify that 2D waveforms (multi-channel) are handled correctly"""
        # Create 2D waveform [channels, samples]
        duration = 1.5
        sample_rate = 16000
        num_samples = int(duration * sample_rate)
        waveform = torch.randn(2, num_samples)  # Stereo
        
        # Extract embedding
        embedding = extract_embedding(waveform, sample_rate)
        
        # Should still produce 192-dimensional embedding
        assert embedding.shape == (192,), f"Expected shape (192,), got {embedding.shape}"
    
    def test_extract_embedding_returns_finite_values(self):
        """Ensure embedding contains no NaN or infinite values"""
        duration = 1.5
        sample_rate = 16000
        num_samples = int(duration * sample_rate)
        waveform = torch.randn(num_samples)
        
        embedding = extract_embedding(waveform, sample_rate)
        
        assert np.all(np.isfinite(embedding)), "Embedding should contain only finite values"


class TestNormalizeEmbedding:
    """Test L2 normalization functionality"""
    
    def test_normalize_produces_unit_vector(self):
        """Validate that L2 normalization produces unit vectors (L2 norm = 1.0)"""
        # Create random embedding
        embedding = np.random.randn(192)
        
        # Normalize
        normalized = normalize_embedding(embedding)
        
        # Compute L2 norm
        norm = np.linalg.norm(normalized)
        
        # Should be 1.0 within tolerance
        assert np.abs(norm - 1.0) < 1e-6, f"Expected L2 norm 1.0, got {norm}"
    
    def test_normalize_preserves_direction(self):
        """Verify that normalization preserves vector direction (only changes magnitude)"""
        embedding = np.random.randn(192)
        normalized = normalize_embedding(embedding)
        
        # Compute cosine similarity (should be 1.0 if direction preserved)
        cosine_sim = np.dot(embedding, normalized) / (np.linalg.norm(embedding) * np.linalg.norm(normalized))
        
        assert np.abs(cosine_sim - 1.0) < 1e-6, "Normalized vector should point in same direction"
    
    def test_normalize_handles_zero_vector(self):
        """Ensure normalization handles near-zero vectors gracefully"""
        embedding = np.zeros(192)
        normalized = normalize_embedding(embedding)
        
        # Should return zero vector unchanged
        assert np.allclose(normalized, embedding), "Zero vector should remain unchanged"


class TestAverageEmbeddings:
    """Test embedding averaging functionality"""
    
    def test_average_computes_element_wise_mean(self):
        """Validate that averaging computes element-wise mean correctly"""
        # Create test embeddings with known values
        emb1 = np.ones(192)
        emb2 = np.ones(192) * 2
        emb3 = np.ones(192) * 3
        
        embeddings = [emb1, emb2, emb3]
        
        # Average
        averaged = average_embeddings(embeddings)
        
        # Expected mean is 2.0 for all elements
        expected = np.ones(192) * 2.0
        
        assert np.allclose(averaged, expected), "Averaged embedding should equal element-wise mean"
    
    def test_average_single_embedding(self):
        """Verify that averaging a single embedding returns the embedding itself"""
        embedding = np.random.randn(192)
        averaged = average_embeddings([embedding])
        
        assert np.allclose(averaged, embedding), "Single embedding average should equal original"
    
    def test_average_preserves_dimensionality(self):
        """Ensure averaged embedding has same dimensions as inputs"""
        embeddings = [np.random.randn(192) for _ in range(5)]
        averaged = average_embeddings(embeddings)
        
        assert averaged.shape == (192,), f"Expected shape (192,), got {averaged.shape}"
    
    def test_average_empty_list_raises_error(self):
        """Verify that averaging empty list raises ValueError"""
        with pytest.raises(ValueError, match="Cannot average empty list"):
            average_embeddings([])


class TestIntegration:
    """Integration tests combining multiple functions"""
    
    def test_extract_normalize_pipeline(self):
        """Test complete pipeline: extract -> normalize"""
        duration = 2.0
        sample_rate = 16000
        num_samples = int(duration * sample_rate)
        waveform = torch.randn(num_samples)
        
        # Extract and normalize
        embedding = extract_embedding(waveform, sample_rate)
        normalized = normalize_embedding(embedding)
        
        # Verify normalized is unit vector
        norm = np.linalg.norm(normalized)
        assert np.abs(norm - 1.0) < 1e-6, f"Normalized embedding should have L2 norm 1.0, got {norm}"
    
    def test_voiceprint_creation_pipeline(self):
        """Test complete voiceprint creation: extract multiple -> normalize each -> average"""
        duration = 1.5
        sample_rate = 16000
        num_samples = int(duration * sample_rate)
        
        # Simulate multiple voice samples
        num_samples_audio = 5
        embeddings = []
        
        for _ in range(num_samples_audio):
            waveform = torch.randn(num_samples)
            embedding = extract_embedding(waveform, sample_rate)
            normalized = normalize_embedding(embedding)
            embeddings.append(normalized)
        
        # Average normalized embeddings
        voiceprint = average_embeddings(embeddings)
        
        # Verify voiceprint properties
        assert voiceprint.shape == (192,), "Voiceprint should be 192-dimensional"
        assert np.all(np.isfinite(voiceprint)), "Voiceprint should contain finite values"
        
        # Note: averaged normalized vectors may not be unit vectors themselves
        # (L2 norm of average of unit vectors is typically < 1.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
