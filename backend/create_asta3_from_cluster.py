"""Create ASTA3 profile from the best cluster of similar samples"""
import torch
import torchaudio
import numpy as np
from pathlib import Path
import json
from datetime import datetime

from model import ModelLoader
from embedding import (
    extract_embedding,
    normalize_embedding,
    average_embeddings,
    compute_cosine_similarity,
    detect_outliers,
    compute_intra_class_stats
)
from audio_utils import load_and_preprocess
from profile_store import ProfileStore
from config import config

def main():
    print("=" * 80)
    print("CREATING ASTA3 FROM BEST CLUSTER")
    print("=" * 80)
    
    # Initialize
    profile_store = ProfileStore(base_path="profiles")
    profile_name = "ASTA3"
    
    # Delete existing ASTA3 if it exists
    if profile_store.profile_exists(profile_name):
        print(f"\n🗑️  Deleting existing {profile_name} profile...")
        profile_store.delete_profile(profile_name)
    
    # Load cluster file list
    with open("best_cluster_files.txt", 'r') as f:
        cluster_files = [line.strip() for line in f.readlines()]
    
    print(f"\n✅ Loaded {len(cluster_files)} files from cluster")
    
    # Load model
    print(f"\nLoading model...")
    model = ModelLoader.get_instance()
    print(f"✅ Model loaded")
    
    # Extract embeddings
    print(f"\nExtracting embeddings...")
    valid_embeddings = []
    processed_files = []
    
    for idx, file_path in enumerate(cluster_files):
        try:
            waveform, meta = load_and_preprocess(file_path)
            embedding = extract_embedding(waveform, config.target_sample_rate)
            normalized = normalize_embedding(embedding)
            valid_embeddings.append(normalized)
            processed_files.append(Path(file_path).name)
            
            if (idx + 1) % 5 == 0:
                print(f"  Processed {idx + 1}/{len(cluster_files)}...")
                
        except Exception as e:
            print(f"  ⚠️ Failed: {Path(file_path).name}: {e}")
    
    print(f"\n✅ Extracted {len(valid_embeddings)} embeddings")
    
    # Compute intra-class stats BEFORE outlier removal
    stats_before = compute_intra_class_stats(valid_embeddings)
    print(f"\n📊 Intra-class stats (before outlier removal):")
    for key, value in stats_before.items():
        print(f"  {key}: {value:.4f}")
    
    # Detect outliers
    outlier_indices = detect_outliers(valid_embeddings, threshold=2.5)
    print(f"\n🔍 Outliers detected: {len(outlier_indices)}")
    if outlier_indices:
        print(f"  Indices: {outlier_indices}")
    
    # Filter outliers
    clean_embeddings = [emb for i, emb in enumerate(valid_embeddings) if i not in outlier_indices]
    if not clean_embeddings:
        clean_embeddings = valid_embeddings
        print(f"  Using all embeddings")
    else:
        print(f"  Clean embeddings: {len(clean_embeddings)}")
    
    # Compute intra-class stats AFTER outlier removal
    stats_after = compute_intra_class_stats(clean_embeddings)
    print(f"\n📊 Intra-class stats (after outlier removal):")
    for key, value in stats_after.items():
        print(f"  {key}: {value:.4f}")
    
    # Compute voiceprint
    voiceprint = average_embeddings(clean_embeddings)
    voiceprint = normalize_embedding(voiceprint)
    
    print(f"\n✅ Voiceprint computed:")
    print(f"  Shape: {voiceprint.shape}")
    print(f"  Norm: {np.linalg.norm(voiceprint):.6f}")
    
    # Set threshold based on stats
    # Use mean - 1.5*std as threshold to be more lenient
    suggested_threshold = max(0.60, stats_after["mean_similarity"] - 1.5 * stats_after["std_similarity"])
    suggested_threshold = min(0.75, suggested_threshold)  # Cap at 0.75
    
    print(f"\n🎯 Suggested threshold: {suggested_threshold:.4f}")
    print(f"  (Based on mean={stats_after['mean_similarity']:.4f}, std={stats_after['std_similarity']:.4f})")
    
    # Save profile
    metadata = {
        "created": datetime.utcnow().isoformat() + "Z",
        "sample_count": len(valid_embeddings),
        "threshold": suggested_threshold,
        "intra_class_stats": stats_after,
        "outliers_detected": outlier_indices,
        "last_verified": None,
        "version": "1.0",
        "training_files": processed_files[:10]
    }
    
    try:
        profile_store.create_profile(profile_name, voiceprint, metadata)
        print(f"\n✅ Profile '{profile_name}' saved successfully")
    except Exception as e:
        print(f"\n❌ Failed to save profile: {e}")
        return
    
    # VERIFICATION TEST
    print(f"\n" + "=" * 80)
    print("SELF-VERIFICATION TEST")
    print("=" * 80)
    
    # Load profile
    profile = profile_store.get_profile(profile_name)
    loaded_voiceprint = profile["voiceprint"]
    threshold = profile["metadata"]["threshold"]
    
    print(f"Threshold: {threshold:.4f}\n")
    
    # Test with first 10 cluster files
    test_files = cluster_files[:10]
    scores = []
    passed = 0
    
    print(f"{'Filename':<25} {'Score':<10} {'Status':<10}")
    print("-" * 45)
    
    for file_path in test_files:
        try:
            waveform, meta = load_and_preprocess(file_path)
            embedding = extract_embedding(waveform, config.target_sample_rate)
            normalized = normalize_embedding(embedding)
            score = compute_cosine_similarity(normalized, loaded_voiceprint)
            scores.append(score)
            
            status = "✅ PASS" if score >= threshold else "❌ FAIL"
            if score >= threshold:
                passed += 1
            
            fname = Path(file_path).name
            print(f"{fname:<25} {score:.4f}    {status}")
            
        except Exception as e:
            print(f"{Path(file_path).name:<25} ERROR: {e}")
    
    # Summary
    print(f"\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    if scores:
        mean_score = np.mean(scores)
        print(f"Mean Score:     {mean_score:.4f}")
        print(f"Min Score:      {np.min(scores):.4f}")
        print(f"Max Score:      {np.max(scores):.4f}")
        print(f"Threshold:      {threshold:.4f}")
        print(f"\nPassed:         {passed}/10")
        print(f"Pass Rate:      {(passed/10)*100:.1f}%")
        
        if passed >= 8 and mean_score > threshold:
            print(f"\n🎉 SUCCESS! System is working correctly!")
            print(f"\nYou can now use ASTA3 profile for verification:")
            print(f"  python test_verification_api.py")
        else:
            print(f"\n⚠️  Results not optimal but profile created.")
            print(f"  Consider: Lower threshold or get better quality samples from same speaker")

if __name__ == "__main__":
    main()
