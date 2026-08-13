"""Debug embedding extraction to see what the model is actually outputting"""
import torch
import torchaudio
import numpy as np
from pathlib import Path

from model import ModelLoader
from audio_utils import load_and_preprocess
from config import config

print("=" * 80)
print("DEBUGGING EMBEDDING EXTRACTION")
print("=" * 80)

# Load model
model = ModelLoader.get_instance()
print(f"\n✅ Model loaded: {type(model)}")
print(f"Model class: {model.__class__.__name__}")

# Check what methods are available
print(f"\nAvailable methods:")
methods = [m for m in dir(model) if not m.startswith('_')]
for method in methods[:20]:
    print(f"  - {method}")

# Load a test file
data_folder = Path("../DATA")
test_file = list(data_folder.glob("*.wav"))[0]
print(f"\nTest file: {test_file.name}")

# Load and preprocess
waveform, meta = load_and_preprocess(str(test_file))
print(f"\nWaveform shape after preprocessing: {waveform.shape}")
print(f"Waveform dtype: {waveform.dtype}")
print(f"Waveform device: {waveform.device}")

# Ensure waveform is 2D
if waveform.dim() == 1:
    waveform = waveform.unsqueeze(0)
print(f"Waveform shape for model input: {waveform.shape}")

# Try encode_batch
print(f"\n" + "=" * 80)
print("TESTING: model.encode_batch()")
print("=" * 80)

with torch.no_grad():
    output = model.encode_batch(waveform)

print(f"Output type: {type(output)}")
print(f"Output shape: {output.shape}")
print(f"Output dtype: {output.dtype}")
print(f"Output device: {output.device}")

# Convert to numpy
output_np = output.squeeze().cpu().numpy()
print(f"\nNumpy shape after squeeze: {output_np.shape}")
print(f"Numpy dtype: {output_np.dtype}")

# Compute L2 norm
norm = np.linalg.norm(output_np)
print(f"L2 norm: {norm:.6f}")

# Check values
print(f"\nEmbedding statistics:")
print(f"  Mean: {np.mean(output_np):.6f}")
print(f"  Std: {np.std(output_np):.6f}")
print(f"  Min: {np.min(output_np):.6f}")
print(f"  Max: {np.max(output_np):.6f}")
print(f"  First 10 values: {output_np[:10]}")

# L2 normalize
normalized = output_np / norm
print(f"\nAfter L2 normalization:")
print(f"  Norm: {np.linalg.norm(normalized):.6f}")
print(f"  Mean: {np.mean(normalized):.6f}")
print(f"  Std: {np.std(normalized):.6f}")

# Test with same file again
print(f"\n" + "=" * 80)
print("TESTING: Same file twice (should give nearly identical embeddings)")
print("=" * 80)

waveform1, _ = load_and_preprocess(str(test_file))
if waveform1.dim() == 1:
    waveform1 = waveform1.unsqueeze(0)

with torch.no_grad():
    emb1 = model.encode_batch(waveform1).squeeze().cpu().numpy()
    emb1 = emb1 / np.linalg.norm(emb1)

waveform2, _ = load_and_preprocess(str(test_file))
if waveform2.dim() == 1:
    waveform2 = waveform2.unsqueeze(0)

with torch.no_grad():
    emb2 = model.encode_batch(waveform2).squeeze().cpu().numpy()
    emb2 = emb2 / np.linalg.norm(emb2)

# Cosine similarity
similarity = np.dot(emb1, emb2)
print(f"Similarity between two extractions of same file: {similarity:.6f}")
print(f"Expected: ~1.0000")

if similarity < 0.999:
    print(f"⚠️ WARNING: Similarity should be ~1.0 for same file!")
else:
    print(f"✅ Good! Extraction is deterministic.")

# Test with two different files
print(f"\n" + "=" * 80)
print("TESTING: Two different files from same speaker")
print("=" * 80)

test_file2 = list(data_folder.glob("*.wav"))[5]
print(f"File 1: {test_file.name}")
print(f"File 2: {test_file2.name}")

waveform_a, _ = load_and_preprocess(str(test_file))
if waveform_a.dim() == 1:
    waveform_a = waveform_a.unsqueeze(0)

waveform_b, _ = load_and_preprocess(str(test_file2))
if waveform_b.dim() == 1:
    waveform_b = waveform_b.unsqueeze(0)

with torch.no_grad():
    emb_a = model.encode_batch(waveform_a).squeeze().cpu().numpy()
    emb_a = emb_a / np.linalg.norm(emb_a)
    
    emb_b = model.encode_batch(waveform_b).squeeze().cpu().numpy()
    emb_b = emb_b / np.linalg.norm(emb_b)

similarity_ab = np.dot(emb_a, emb_b)
print(f"\nSimilarity between two different files: {similarity_ab:.6f}")
print(f"Expected for same speaker: 0.75 - 0.90")

if similarity_ab < 0.60:
    print(f"⚠️ WARNING: Very low similarity! Possible issues:")
    print(f"   - Files are from different speakers")
    print(f"   - Audio quality issues")
    print(f"   - Model not extracting correct embeddings")
else:
    print(f"✅ Similarity in expected range!")

# Check if embeddings have reasonable diversity
print(f"\n" + "=" * 80)
print("TESTING: Embedding diversity across 5 files")
print("=" * 80)

test_files = list(data_folder.glob("*.wav"))[:5]
embeddings = []

for tf in test_files:
    wf, _ = load_and_preprocess(str(tf))
    if wf.dim() == 1:
        wf = wf.unsqueeze(0)
    with torch.no_grad():
        emb = model.encode_batch(wf).squeeze().cpu().numpy()
        emb = emb / np.linalg.norm(emb)
        embeddings.append(emb)

# Compute all pairwise similarities
print(f"\nPairwise cosine similarities:")
for i in range(len(embeddings)):
    for j in range(i+1, len(embeddings)):
        sim = np.dot(embeddings[i], embeddings[j])
        print(f"  File {i} vs File {j}: {sim:.4f}")

mean_sim = np.mean([np.dot(embeddings[i], embeddings[j]) 
                     for i in range(len(embeddings)) 
                     for j in range(i+1, len(embeddings))])
print(f"\nMean pairwise similarity: {mean_sim:.4f}")
print(f"Expected for same speaker: 0.75 - 0.85")

if mean_sim < 0.60:
    print(f"\n❌ CRITICAL: Mean similarity is too low!")
    print(f"   This suggests the audio files are NOT from the same speaker,")
    print(f"   or there's a fundamental issue with the audio data.")
else:
    print(f"\n✅ Similarity looks reasonable!")
