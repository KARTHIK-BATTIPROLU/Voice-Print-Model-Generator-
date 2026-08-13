"""
Analyze the DATA folder to find which samples are actually from the same speaker
"""
import torch
import numpy as np
from pathlib import Path
from model import ModelLoader
from audio_utils import load_and_preprocess
from embedding import extract_embedding, normalize_embedding, compute_cosine_similarity

print("=" * 80)
print("ANALYZING YOUR VOICE SAMPLES")
print("=" * 80)

# Load model
model = ModelLoader.get_instance()
data_folder = Path("../DATA")
wav_files = sorted(list(data_folder.glob("*.wav")))

print(f"\nExtracting embeddings from {len(wav_files)} files...")
embeddings = []
file_names = []

for idx, wav_path in enumerate(wav_files):
    try:
        waveform, _ = load_and_preprocess(str(wav_path))
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)
        
        with torch.no_grad():
            emb = model.encode_batch(waveform).squeeze().cpu().numpy()
            emb = emb / np.linalg.norm(emb)
        
        embeddings.append(emb)
        file_names.append(wav_path.name)
        
        if (idx + 1) % 25 == 0:
            print(f"  Processed {idx + 1}/{len(wav_files)}...")
            
    except Exception as e:
        print(f"  Skipped {wav_path.name}: {e}")

embeddings = np.array(embeddings)
print(f"\n✅ Extracted {len(embeddings)} embeddings\n")

# Compute similarity matrix
print("Computing pairwise similarities...")
n = len(embeddings)
sim_matrix = np.zeros((n, n))

for i in range(n):
    for j in range(n):
        sim_matrix[i, j] = np.dot(embeddings[i], embeddings[j])

print("✅ Similarity matrix computed\n")

# Analyze the data
print("=" * 80)
print("ANALYSIS RESULTS")
print("=" * 80)

# Overall statistics
all_sims = []
for i in range(n):
    for j in range(i+1, n):
        all_sims.append(sim_matrix[i, j])

all_sims = np.array(all_sims)
print(f"\nOverall Statistics:")
print(f"  Mean similarity: {np.mean(all_sims):.4f}")
print(f"  Std dev: {np.std(all_sims):.4f}")
print(f"  Min: {np.min(all_sims):.4f}")
print(f"  Max: {np.max(all_sims):.4f}")

# Find clusters
print(f"\n" + "=" * 80)
print("FINDING SPEAKER GROUPS")
print("=" * 80)

# Use hierarchical approach: start with high similarity
threshold = 0.70
groups = []
assigned = set()

for i in range(n):
    if i in assigned:
        continue
    
    # Find all samples highly similar to this one
    group = [i]
    for j in range(n):
        if j != i and j not in assigned and sim_matrix[i, j] >= threshold:
            group.append(j)
    
    if len(group) >= 5:  # Only keep groups with 5+ samples
        for idx in group:
            assigned.add(idx)
        groups.append(group)

print(f"\nFound {len(groups)} distinct speaker groups (threshold={threshold}):\n")

for g_idx, group in enumerate(groups, 1):
    group_files = [file_names[i] for i in group]
    
    # Compute internal similarity
    internal_sims = []
    for i in range(len(group)):
        for j in range(i+1, len(group)):
            internal_sims.append(sim_matrix[group[i], group[j]])
    
    mean_sim = np.mean(internal_sims) if internal_sims else 0
    
    print(f"Group {g_idx}: {len(group)} samples, mean similarity: {mean_sim:.4f}")
    print(f"  Files: {group_files[:10]}")  # Show first 10
    if len(group_files) > 10:
        print(f"  ... and {len(group_files)-10} more")
    print()

# Unassigned samples
unassigned = [i for i in range(n) if i not in assigned]
if unassigned:
    print(f"Unassigned samples: {len(unassigned)}")
    print(f"  These don't strongly match any group")
    print(f"  Files: {[file_names[i] for i in unassigned[:20]]}")
    if len(unassigned) > 20:
        print(f"  ... and {len(unassigned)-20} more")

# CRITICAL FINDING
print(f"\n" + "=" * 80)
print("CRITICAL FINDING")
print("=" * 80)

if np.mean(all_sims) < 0.60:
    print(f"\n❌ PROBLEM DETECTED:")
    print(f"   Mean similarity: {np.mean(all_sims):.4f} (should be 0.75-0.85 for same speaker)")
    print(f"\n   Your DATA folder contains recordings from MULTIPLE DIFFERENT PEOPLE!")
    print(f"\n   For voice biometrics to work, you need:")
    print(f"   1. Record 50-100 samples of ONLY YOUR VOICE")
    print(f"   2. Same microphone, same environment")
    print(f"   3. Natural speech, various phrases")
    print(f"   4. Expected similarity: 0.75-0.85")
    print(f"\n   Current data has too much variation to create a reliable voiceprint.")
else:
    print(f"\n✅ Data looks good!")
    print(f"   Mean similarity: {np.mean(all_sims):.4f}")
    print(f"   This is acceptable for voice biometrics")

# Save detailed analysis
analysis = {
    "total_files": len(wav_files),
    "mean_similarity": float(np.mean(all_sims)),
    "std_similarity": float(np.std(all_sims)),
    "min_similarity": float(np.min(all_sims)),
    "max_similarity": float(np.max(all_sims)),
    "num_groups": len(groups),
    "group_sizes": [len(g) for g in groups],
    "unassigned_count": len(unassigned)
}

import json
with open("VOICE_ANALYSIS.json", "w") as f:
    json.dump(analysis, f, indent=2)

print(f"\n✅ Detailed analysis saved to: VOICE_ANALYSIS.json")
print("=" * 80)
