"""
Complete end-to-end test: Create ASTA3 profile and verify with same samples
"""
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
    print("ASTA3 PROFILE CREATION AND VALIDATION TEST")
    print("=" * 80)
    
    # Initialize
    profile_store = ProfileStore(base_path="profiles")
    profile_name = "ASTA3"
    data_folder = Path("../DATA")
    
    # Delete existing ASTA3 if it exists
    if profile_store.profile_exists(profile_name):
        print(f"\n🗑️  Deleting existing {profile_name} profile...")
        profile_store.delete_profile(profile_name)
        print(f"✅ Deleted {profile_name}")
    
    # Step 1: Load model
    print(f"\n" + "=" * 80)
    print("STEP 1: LOADING MODEL")
    print("=" * 80)
    try:
        model = ModelLoader.get_instance()
        print("✅ Model loaded successfully")
        print(f"   Model type: {type(model)}")
        print(f"   Model ready: {ModelLoader.is_loaded()}")
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return
    
    # Step 2: Collect WAV files
    print(f"\n" + "=" * 80)
    print("STEP 2: COLLECTING TRAINING SAMPLES")
    print("=" * 80)
    wav_files = sorted(list(data_folder.glob("*.wav")))[:50]  # Use first 50 samples
    print(f"✅ Found {len(wav_files)} samples in DATA folder")
    print(f"   Using first 50 for enrollment")
    
    # Step 3: Extract embeddings
    print(f"\n" + "=" * 80)
    print("STEP 3: EXTRACTING EMBEDDINGS")
    print("=" * 80)
    
    valid_embeddings = []
    processed_files = []
    rejected_count = 0
    
    for idx, wav_path in enumerate(wav_files):
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
            
            if (idx + 1) % 10 == 0:
                print(f"   Processed {idx + 1}/{len(wav_files)} samples...")
                print(f"      Last: {wav_path.name}, Norm: {norm:.6f}, Shape: {normalized.shape}")
            
        except Exception as e:
            print(f"   ⚠️ Failed to process {wav_path.name}: {e}")
            rejected_count += 1
    
    print(f"\n✅ Embedding extraction complete:")
    print(f"   Valid: {len(valid_embeddings)}")
    print(f"   Rejected: {rejected_count}")
    print(f"   Embedding shape: {valid_embeddings[0].shape}")
    print(f"   Embedding dtype: {valid_embeddings[0].dtype}")
    
    # Step 4: Detect outliers
    print(f"\n" + "=" * 80)
    print("STEP 4: OUTLIER DETECTION")
    print("=" * 80)
    
    outlier_indices = detect_outliers(valid_embeddings, threshold=config.enrollment.outlier_threshold)
    print(f"✅ Outliers detected: {len(outlier_indices)}")
    if outlier_indices:
        print(f"   Outlier indices: {outlier_indices}")
    
    # Filter outliers
    clean_embeddings = [emb for i, emb in enumerate(valid_embeddings) if i not in outlier_indices]
    if not clean_embeddings:
        clean_embeddings = valid_embeddings
        print(f"   Using all embeddings (no clean embeddings after filtering)")
    else:
        print(f"   Clean embeddings: {len(clean_embeddings)}")
    
    # Step 5: Compute voiceprint
    print(f"\n" + "=" * 80)
    print("STEP 5: COMPUTING VOICEPRINT")
    print("=" * 80)
    
    voiceprint = average_embeddings(clean_embeddings)
    voiceprint = normalize_embedding(voiceprint)
    
    print(f"✅ Voiceprint computed:")
    print(f"   Shape: {voiceprint.shape}")
    print(f"   Norm: {np.linalg.norm(voiceprint):.6f}")
    print(f"   Mean: {np.mean(voiceprint):.6f}")
    print(f"   Std: {np.std(voiceprint):.6f}")
    print(f"   Min: {np.min(voiceprint):.6f}")
    print(f"   Max: {np.max(voiceprint):.6f}")
    
    # Step 6: Compute intra-class stats
    print(f"\n" + "=" * 80)
    print("STEP 6: COMPUTING INTRA-CLASS STATISTICS")
    print("=" * 80)
    
    stats = compute_intra_class_stats(valid_embeddings)
    print(f"✅ Intra-class statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value:.4f}")
    
    # Step 7: Save profile
    print(f"\n" + "=" * 80)
    print("STEP 7: SAVING PROFILE")
    print("=" * 80)
    
    metadata = {
        "created": datetime.utcnow().isoformat() + "Z",
        "sample_count": len(valid_embeddings),
        "threshold": 0.70,  # Start with 0.70 threshold
        "intra_class_stats": stats,
        "outliers_detected": outlier_indices,
        "last_verified": None,
        "version": "1.0",
        "training_files": processed_files[:10]  # Store first 10 for reference
    }
    
    try:
        profile_store.create_profile(profile_name, voiceprint, metadata)
        print(f"✅ Profile '{profile_name}' saved successfully")
        print(f"   Location: profiles/{profile_name}/")
    except Exception as e:
        print(f"❌ Failed to save profile: {e}")
        return
    
    # Step 8: SELF-VERIFICATION TEST
    print(f"\n" + "=" * 80)
    print("STEP 8: SELF-VERIFICATION TEST (CRITICAL)")
    print("=" * 80)
    print(f"Testing with 10 samples from training set...")
    print(f"Expected: High scores (> 0.70) since these were used for training\n")
    
    # Load saved profile
    profile = profile_store.get_profile(profile_name)
    loaded_voiceprint = profile["voiceprint"]
    threshold = profile["metadata"]["threshold"]
    
    print(f"Loaded voiceprint shape: {loaded_voiceprint.shape}")
    print(f"Loaded voiceprint norm: {np.linalg.norm(loaded_voiceprint):.6f}")
    print(f"Threshold: {threshold}\n")
    
    test_files = wav_files[:10]  # Use first 10 files for testing
    scores = []
    passed = 0
    failed = 0
    
    print(f"{'Filename':<20} {'Score':<10} {'Status':<10}")
    print("-" * 40)
    
    for wav_path in test_files:
        try:
            # Load and preprocess
            waveform, meta = load_and_preprocess(str(wav_path))
            
            # Extract embedding
            embedding = extract_embedding(waveform, config.target_sample_rate)
            
            # Normalize
            normalized = normalize_embedding(embedding)
            
            # Compute similarity
            score = compute_cosine_similarity(normalized, loaded_voiceprint)
            scores.append(score)
            
            status = "✅ PASS" if score >= threshold else "❌ FAIL"
            if score >= threshold:
                passed += 1
            else:
                failed += 1
            
            print(f"{wav_path.name:<20} {score:.4f}    {status}")
            
        except Exception as e:
            print(f"{wav_path.name:<20} ERROR: {e}")
            failed += 1
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS SUMMARY")
    print("=" * 80)
    
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
        print(f"\nPassed:         {passed}/10")
        print(f"Failed:         {failed}/10")
        print(f"Pass Rate:      {(passed/10)*100:.1f}%")
        
        # Success criteria
        print(f"\n" + "=" * 80)
        print("SUCCESS CRITERIA CHECK")
        print("=" * 80)
        
        criteria_met = 0
        criteria_total = 3
        
        print(f"1. Mean score > 0.70: ", end="")
        if mean_score > 0.70:
            print(f"✅ YES ({mean_score:.4f})")
            criteria_met += 1
        else:
            print(f"❌ NO ({mean_score:.4f})")
        
        print(f"2. At least 9/10 samples pass: ", end="")
        if passed >= 9:
            print(f"✅ YES ({passed}/10)")
            criteria_met += 1
        else:
            print(f"❌ NO ({passed}/10)")
        
        print(f"3. Min score > 0.65: ", end="")
        if min_score > 0.65:
            print(f"✅ YES ({min_score:.4f})")
            criteria_met += 1
        else:
            print(f"❌ NO ({min_score:.4f})")
        
        print(f"\n" + "=" * 80)
        if criteria_met == criteria_total:
            print("🎉 ALL CRITERIA MET - SYSTEM IS WORKING CORRECTLY!")
        else:
            print(f"⚠️  CRITERIA MET: {criteria_met}/{criteria_total}")
            print("⚠️  SYSTEM NEEDS INVESTIGATION")
        print("=" * 80)
    else:
        print("❌ No scores computed - all verification attempts failed")
    
    # Step 9: Test with a different sample (not in training)
    print(f"\n" + "=" * 80)
    print("STEP 9: VERIFICATION WITH UNSEEN SAMPLE")
    print("=" * 80)
    
    if len(wav_files) > 50:
        test_unseen = wav_files[50]  # Sample not used in training
        print(f"Testing with: {test_unseen.name} (not in training set)")
        
        try:
            waveform, meta = load_and_preprocess(str(test_unseen))
            embedding = extract_embedding(waveform, config.target_sample_rate)
            normalized = normalize_embedding(embedding)
            score = compute_cosine_similarity(normalized, loaded_voiceprint)
            
            status = "✅ PASS" if score >= threshold else "❌ FAIL"
            print(f"Score: {score:.4f} - {status}")
            
            if score >= threshold:
                print("✅ Unseen sample verified successfully (same speaker)")
            else:
                print(f"⚠️  Unseen sample failed (score < {threshold})")
        except Exception as e:
            print(f"❌ Error testing unseen sample: {e}")
    else:
        print("⚠️  Not enough samples to test unseen data")
    
    print(f"\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
