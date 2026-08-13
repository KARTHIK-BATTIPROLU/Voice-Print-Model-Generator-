import os
import shutil
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import torch

# Ensure backend directory is in python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

from config import config
from model import ModelLoader
from profile_store import ProfileStore
from audio_utils import load_and_preprocess
from embedding import (
    extract_embedding,
    normalize_embedding,
    average_embeddings,
    detect_outliers,
    compute_intra_class_stats
)

def enroll_asta():
    print("=" * 60)
    print("Enroll Asta Voice Print Profile")
    print("=" * 60)
    
    # 1. Initialize ProfileStore and delete existing profiles for Asta/ASTA
    store = ProfileStore(base_path=config.storage_path)
    
    for name in ["ASTA", "Asta"]:
        if store.profile_exists(name):
            print(f"Removing existing profile '{name}'...")
            store.delete_profile(name)
        elif (Path(config.storage_path) / name).exists():
            print(f"Cleaning up directory '{name}'...")
            shutil.rmtree(Path(config.storage_path) / name, ignore_errors=True)
            
    # 2. Get list of audio files
    data_dir = Path("c:/Users/Karthik/OneDrive/Desktop/Voice Print Model Generator/DATA")
    if not data_dir.exists():
        print(f"Error: DATA directory does not exist at {data_dir}")
        return
        
    wav_files = sorted(list(data_dir.glob("*.wav")))
    total_files = len(wav_files)
    print(f"Found {total_files} WAV files in DATA directory.")
    
    if total_files < 10:
        print("Error: Minimum 10 recordings required for enrollment.")
        return
        
    # 3. Pre-load ModelLoader
    print("Initializing ModelLoader singleton...")
    ModelLoader.get_instance()
    
    # 4. Process files
    valid_embeddings = []
    rejected_count = 0
    filenames = []
    
    print("\nProcessing audio files:")
    for idx, filepath in enumerate(wav_files):
        print(f"[{idx+1}/{total_files}] Processing {filepath.name}...", end="\r")
        try:
            # Preprocess WAV
            waveform, meta = load_and_preprocess(str(filepath))
            
            # Extract and normalize embedding
            embedding = extract_embedding(waveform, config.target_sample_rate)
            normalized = normalize_embedding(embedding)
            
            valid_embeddings.append(normalized)
            filenames.append(filepath.name)
        except Exception as e:
            # Print on a new line to avoid overwriting progress
            print(f"\n[Warning] Skipped {filepath.name}: {e}")
            rejected_count += 1
            
    print(f"\n\nProcessing complete:")
    print(f"- Total processed successfully: {len(valid_embeddings)}")
    print(f"- Total rejected/skipped: {rejected_count}")
    
    if len(valid_embeddings) < 10:
        print("Error: Not enough valid samples (minimum 10 required) to generate voiceprint.")
        return
        
    # 5. Outlier Detection
    print("\nRunning outlier detection...")
    outliers = detect_outliers(valid_embeddings, threshold=config.enrollment.outlier_threshold)
    print(f"Detected {len(outliers)} outlier files:")
    for out_idx in outliers:
        print(f"  - Outlier: {filenames[out_idx]}")
        
    # Filter out outliers for voiceprint generation
    clean_embeddings = [emb for i, emb in enumerate(valid_embeddings) if i not in outliers]
    if not clean_embeddings:
        print("Warning: All files marked as outliers. Falling back to all valid files.")
        clean_embeddings = valid_embeddings
        
    # 6. Average and normalize final voiceprint
    print("\nGenerating averaged voiceprint...")
    voiceprint = average_embeddings(clean_embeddings)
    voiceprint = normalize_embedding(voiceprint)
    
    # 7. Compute cohesion stats
    stats = compute_intra_class_stats(valid_embeddings)
    print("\nIntra-class Cohesion Statistics:")
    print(f"  - Mean Similarity: {stats['mean_similarity']:.4f}")
    print(f"  - Std Deviation:   {stats['std_similarity']:.4f}")
    print(f"  - Min Similarity:  {stats['min_similarity']:.4f}")
    print(f"  - Max Similarity:  {stats['max_similarity']:.4f}")
    
    # 8. Save profile
    metadata = {
        "created": datetime.utcnow().isoformat() + "Z",
        "sample_count": len(valid_embeddings),
        "threshold": config.default_threshold,
        "intra_class_stats": stats,
        "outliers_detected": outliers,
        "last_verified": None,
        "version": "1.0"
    }
    
    profile_name = "Asta"
    print(f"\nSaving profile '{profile_name}'...")
    success = store.create_profile(profile_name, voiceprint, metadata)
    
    if success:
        print(f"✅ Success! Profile '{profile_name}' created successfully with {len(valid_embeddings)} samples.")
    else:
        print("❌ Error: Failed to save profile.")

if __name__ == "__main__":
    enroll_asta()
