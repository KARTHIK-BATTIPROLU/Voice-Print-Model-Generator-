"""
Create ONE complete KARTHIK profile using ALL samples from DATA folder
This is the FINAL profile that should recognize your real-time voice
"""
import torch
import torchaudio
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import shutil

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
    print("CREATING FINAL KARTHIK PROFILE")
    print("Using ALL samples from DATA folder (sample_0004 to sample_0174)")
    print("=" * 80)
    
    # Initialize
    profile_store = ProfileStore(base_path="profiles")
    profile_name = "KARTHIK"
    data_folder = Path("../DATA")
    
    # Step 1: DELETE ALL EXISTING PROFILES
    print(f"\n🗑️  DELETING ALL EXISTING PROFILES...")
    existing_profiles = profile_store.list_profiles()
    for profile in existing_profiles:
        try:
            profile_store.delete_profile(profile['name'])
            print(f"   Deleted: {profile['name']}")
        except Exception as e:
            print(f"   Error deleting {profile['name']}: {e}")
    
    # Also manually delete profiles folder
    profiles_folder = Path("profiles")
    if profiles_folder.exists():
        shutil.rmtree(profiles_folder)
        print(f"   Deleted profiles folder")
    profiles_folder.mkdir(exist_ok=True)
    
    print(f"✅ All existing profiles deleted\n")
    
    # Step 2: Load model
    print(f"Loading model...")
    model = ModelLoader.get_instance()
    print(f"✅ Model loaded\n")
    
    # Step 3: Get ALL WAV files
    print(f"Scanning DATA folder...")
    all_wav_files = sorted(list(data_folder.glob("*.wav")))
    print(f"✅ Found {len(all_wav_files)} WAV files\n")
    
    # Step 4: Extract embeddings from ALL files
    print(f"=" * 80)
    print(f"EXTRACTING EMBEDDINGS FROM ALL {len(all_wav_files)} FILES")
    print(f"=" * 80)
    
    valid_embeddings = []
    processed_files = []
    skipped = []
    
    for idx, wav_path in enumerate(all_wav_files):
        try:
            # Load and preprocess
            waveform, meta = load_and_preprocess(str(wav_path))
            
            # Extract embedding
            embedding = extract_embedding(waveform, config.target_sample_rate)
            
            # Normalize
            normalized = normalize_embedding(embedding)
            
            # Verify normalization
            norm = np.linalg.norm(normalized)
            
            valid_embeddings.append(normalized)
            processed_files.append(wav_path.name)
            
            if (idx + 1) % 25 == 0 or (idx + 1) == len(all_wav_files):
                print(f"   Processed {idx + 1}/{len(all_wav_files)} samples... (Last: {wav_path.name}, Norm: {norm:.6f})")
            
        except Exception as e:
            print(f"   ⚠️ Skipped {wav_path.name}: {e}")
            skipped.append((wav_path.name, str(e)))
    
    print(f"\n✅ Embedding extraction complete:")
    print(f"   Valid: {len(valid_embeddings)}")
    print(f"   Skipped: {len(skipped)}")
    if skipped:
        print(f"   Skipped files:")
        for name, err in skipped[:10]:  # Show first 10
            print(f"     - {name}: {err}")
    
    if len(valid_embeddings) < 10:
        print(f"\n❌ ERROR: Not enough valid samples ({len(valid_embeddings)})")
        return
    
    # Step 5: Compute intra-class stats BEFORE outlier removal
    print(f"\n" + "=" * 80)
    print(f"COMPUTING QUALITY METRICS")
    print(f"=" * 80)
    
    stats_before = compute_intra_class_stats(valid_embeddings)
    print(f"Intra-class statistics (ALL samples):")
    for key, value in stats_before.items():
        print(f"  {key}: {value:.4f}")
    
    # Step 6: Detect outliers
    print(f"\n🔍 Detecting outliers...")
    outlier_indices = detect_outliers(valid_embeddings, threshold=2.5)
    print(f"   Outliers detected: {len(outlier_indices)}")
    if outlier_indices and len(outlier_indices) < 20:
        print(f"   Outlier indices: {outlier_indices}")
    
    # Step 7: Filter outliers
    clean_embeddings = [emb for i, emb in enumerate(valid_embeddings) if i not in outlier_indices]
    if not clean_embeddings:
        print(f"   WARNING: No clean embeddings after filtering, using all")
        clean_embeddings = valid_embeddings
    else:
        print(f"   Clean embeddings: {len(clean_embeddings)}")
    
    # Compute stats after outlier removal
    stats_after = compute_intra_class_stats(clean_embeddings)
    print(f"\nIntra-class statistics (after outlier removal):")
    for key, value in stats_after.items():
        print(f"  {key}: {value:.4f}")
    
    # Step 8: Compute voiceprint
    print(f"\n" + "=" * 80)
    print(f"COMPUTING FINAL VOICEPRINT")
    print(f"=" * 80)
    
    voiceprint = average_embeddings(clean_embeddings)
    voiceprint = normalize_embedding(voiceprint)
    
    print(f"✅ Voiceprint computed:")
    print(f"   Shape: {voiceprint.shape}")
    print(f"   Norm: {np.linalg.norm(voiceprint):.6f}")
    print(f"   Mean: {np.mean(voiceprint):.6f}")
    print(f"   Std: {np.std(voiceprint):.6f}")
    
    # Step 9: Set threshold based on stats
    # Use mean - 2*std to be more inclusive
    suggested_threshold = stats_after["mean_similarity"] - 2.0 * stats_after["std_similarity"]
    suggested_threshold = max(0.50, min(0.75, suggested_threshold))  # Clamp between 0.50 and 0.75
    
    print(f"\n🎯 Suggested threshold: {suggested_threshold:.4f}")
    print(f"   (Based on mean={stats_after['mean_similarity']:.4f}, std={stats_after['std_similarity']:.4f})")
    
    # Step 10: Save profile
    print(f"\n" + "=" * 80)
    print(f"SAVING PROFILE: {profile_name}")
    print(f"=" * 80)
    
    metadata = {
        "created": datetime.utcnow().isoformat() + "Z",
        "sample_count": len(valid_embeddings),
        "clean_sample_count": len(clean_embeddings),
        "threshold": suggested_threshold,
        "intra_class_stats": stats_after,
        "outliers_detected": outlier_indices,
        "last_verified": None,
        "version": "2.0",
        "description": "Complete KARTHIK profile using all DATA samples",
        "total_files_processed": len(all_wav_files),
        "files_skipped": len(skipped)
    }
    
    try:
        profile_store.create_profile(profile_name, voiceprint, metadata)
        print(f"✅ Profile '{profile_name}' saved successfully")
        print(f"   Location: profiles/{profile_name}/")
    except Exception as e:
        print(f"❌ Failed to save profile: {e}")
        return
    
    # Step 11: VERIFICATION TEST
    print(f"\n" + "=" * 80)
    print(f"SELF-VERIFICATION TEST (20 RANDOM SAMPLES)")
    print(f"=" * 80)
    
    # Load saved profile
    profile = profile_store.get_profile(profile_name)
    loaded_voiceprint = profile["voiceprint"]
    threshold = profile["metadata"]["threshold"]
    
    print(f"Threshold: {threshold:.4f}\n")
    
    # Test with 20 random samples
    import random
    test_files = random.sample(all_wav_files, min(20, len(all_wav_files)))
    scores = []
    passed = 0
    failed = 0
    
    print(f"{'Filename':<25} {'Score':<10} {'Status':<10}")
    print("-" * 45)
    
    for wav_path in test_files:
        try:
            waveform, meta = load_and_preprocess(str(wav_path))
            embedding = extract_embedding(waveform, config.target_sample_rate)
            normalized = normalize_embedding(embedding)
            score = compute_cosine_similarity(normalized, loaded_voiceprint)
            scores.append(score)
            
            status = "✅ PASS" if score >= threshold else "❌ FAIL"
            if score >= threshold:
                passed += 1
            else:
                failed += 1
            
            print(f"{wav_path.name:<25} {score:.4f}    {status}")
            
        except Exception as e:
            print(f"{wav_path.name:<25} ERROR: {e}")
            failed += 1
    
    # Summary
    print(f"\n" + "=" * 80)
    print(f"RESULTS")
    print(f"=" * 80)
    
    if scores:
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        min_score = np.min(scores)
        max_score = np.max(scores)
        
        print(f"Mean Score:     {mean_score:.4f}")
        print(f"Std Dev:        {std_score:.4f}")
        print(f"Min Score:      {min_score:.4f}")
        print(f"Max Score:      {max_score:.4f}")
        print(f"Threshold:      {threshold:.4f}")
        print(f"\nPassed:         {passed}/20")
        print(f"Failed:         {failed}/20")
        print(f"Pass Rate:      {(passed/20)*100:.1f}%")
        
        print(f"\n" + "=" * 80)
        if passed >= 18:  # 90% pass rate
            print(f"🎉 SUCCESS! Profile is working well!")
            print(f"\nYou can now:")
            print(f"1. Test with the web interface")
            print(f"2. Test with real-time audio recordings")
            print(f"3. All samples from DATA folder should verify")
        elif passed >= 15:  # 75% pass rate
            print(f"⚠️  Profile is working but could be better")
            print(f"   Consider lowering threshold to {threshold - 0.05:.4f}")
        else:
            print(f"⚠️  Low pass rate - investigating...")
            print(f"   Mean similarity in training: {stats_after['mean_similarity']:.4f}")
            print(f"   This might indicate voice variation in recordings")
    
    print(f"=" * 80)
    
    # Step 12: Create summary file
    summary = {
        "profile_name": profile_name,
        "created": datetime.utcnow().isoformat() + "Z",
        "total_samples": len(all_wav_files),
        "valid_samples": len(valid_embeddings),
        "clean_samples": len(clean_embeddings),
        "threshold": threshold,
        "intra_class_stats": stats_after,
        "test_results": {
            "passed": passed,
            "failed": failed,
            "mean_score": float(mean_score) if scores else 0,
            "pass_rate": (passed/20) if scores else 0
        }
    }
    
    with open("KARTHIK_PROFILE_SUMMARY.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Summary saved to: KARTHIK_PROFILE_SUMMARY.json")

if __name__ == "__main__":
    main()
