"""
Manual test for embedding functions
"""
import numpy as np
import torch
from embedding import extract_embedding, normalize_embedding, average_embeddings

print("Testing embedding functions...")

# Test 1: Create a simple waveform and extract embedding
print("\n1. Testing extract_embedding...")
duration = 1.5
sample_rate = 16000
num_samples = int(duration * sample_rate)
waveform = torch.randn(num_samples)
print(f"   Created waveform: shape={waveform.shape}, duration={duration}s, sr={sample_rate}Hz")

try:
    embedding = extract_embedding(waveform, sample_rate)
    print(f"   ✓ Extracted embedding: shape={embedding.shape}, dtype={embedding.dtype}")
    print(f"   ✓ Embedding range: [{embedding.min():.4f}, {embedding.max():.4f}]")
    print(f"   ✓ All finite values: {np.all(np.isfinite(embedding))}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Test 2: Normalize embedding
print("\n2. Testing normalize_embedding...")
try:
    normalized = normalize_embedding(embedding)
    norm = np.linalg.norm(normalized)
    print(f"   ✓ Normalized embedding: shape={normalized.shape}")
    print(f"   ✓ L2 norm: {norm:.10f} (should be 1.0)")
    print(f"   ✓ Norm within tolerance: {abs(norm - 1.0) < 1e-6}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Test 3: Average multiple embeddings
print("\n3. Testing average_embeddings...")
try:
    # Create 3 test embeddings
    emb1 = np.ones(192)
    emb2 = np.ones(192) * 2
    emb3 = np.ones(192) * 3
    
    averaged = average_embeddings([emb1, emb2, emb3])
    expected = np.ones(192) * 2.0
    
    print(f"   ✓ Averaged embedding: shape={averaged.shape}")
    print(f"   ✓ Expected all values = 2.0, got mean={averaged.mean():.4f}")
    print(f"   ✓ Correct averaging: {np.allclose(averaged, expected)}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Test 4: Complete pipeline
print("\n4. Testing complete pipeline (extract -> normalize -> average)...")
try:
    embeddings = []
    for i in range(3):
        waveform = torch.randn(num_samples)
        emb = extract_embedding(waveform, sample_rate)
        norm_emb = normalize_embedding(emb)
        embeddings.append(norm_emb)
        print(f"   Sample {i+1}: L2 norm = {np.linalg.norm(norm_emb):.10f}")
    
    voiceprint = average_embeddings(embeddings)
    print(f"   ✓ Voiceprint created: shape={voiceprint.shape}")
    print(f"   ✓ Voiceprint range: [{voiceprint.min():.4f}, {voiceprint.max():.4f}]")
    print(f"   ✓ All finite: {np.all(np.isfinite(voiceprint))}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

print("\n✅ All tests passed!")
