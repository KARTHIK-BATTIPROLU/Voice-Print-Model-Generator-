"""Find a cluster of similar samples to create a working demo profile"""
import torch
import torchaudio
import numpy as np
from pathlib import Path
from model import ModelLoader
from audio_utils import load_and_preprocess

print("=" * 80)
print("FINDING SIMILAR SAMPLES FOR DEMO")
print("=" * 80)

# Load model
model = ModelLoader.get_instance()
print("✅ Model loaded\n")

# Load all samples
data_folder = Path("../DATA")
wav_files = sorted(list(data_folder.glob("*.wav")))[:100]  # Check first 100

print(f"Extracting embeddings from {len(wav_files)} files...")
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
        
        if (idx + 1) % 20 == 0:
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

# Find the best cluster using a simple greedy approach
# Start with each sample and find its most similar neighbors
best_cluster_score = 0
best_cluster_indices = []
best_seed_idx = 0

for seed_idx in range(n):
    # Get similarities to this seed
    sims = sim_matrix[seed_idx]
    
    # Find top 20 most similar samples (including itself)
    top_indices = np.argsort(sims)[::-1][:20]
    
    # Compute mean pairwise similarity within this cluster
    cluster_sims = []
    for i in range(len(top_indices)):
        for j in range(i+1, len(top_indices)):
            cluster_sims.append(sim_matrix[top_indices[i], top_indices[j]])
    
    mean_cluster_sim = np.mean(cluster_sims)
    
    if mean_cluster_sim > best_cluster_score:
        best_cluster_score = mean_cluster_sim
        best_cluster_indices = top_indices
        best_seed_idx = seed_idx

print(f"=" * 80)
print(f"BEST CLUSTER FOUND")
print(f"=" * 80)
print(f"Seed file: {file_names[best_seed_idx]}")
print(f"Cluster size: {len(best_cluster_indices)} samples")
print(f"Mean intra-cluster similarity: {best_cluster_score:.4f}")
print(f"\nCluster members:")

for idx in best_cluster_indices:
    sim_to_seed = sim_matrix[best_seed_idx, idx]
    print(f"  {file_names[idx]:<25} similarity to seed: {sim_to_seed:.4f}")

# Save cluster file list
cluster_files = [file_names[idx] for idx in best_cluster_indices]
output_file = "best_cluster_files.txt"
with open(output_file, 'w') as f:
    for fname in cluster_files:
        f.write(f"../DATA/{fname}\n")

print(f"\n✅ Cluster file list saved to: {output_file}")
print(f"\nTo create ASTA3 profile with this cluster, run:")
print(f"  python create_asta3_from_cluster.py")
