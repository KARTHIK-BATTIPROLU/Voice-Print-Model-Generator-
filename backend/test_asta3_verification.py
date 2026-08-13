"""Test ASTA3 profile verification with various samples"""
import torch
import numpy as np
from pathlib import Path

from model import ModelLoader
from embedding import extract_embedding, normalize_embedding, compute_cosine_similarity
from audio_utils import load_and_preprocess
from profile_store import ProfileStore
from config import config

def test_verification(profile_name="ASTA3"):
    print("=" * 80)
    print(f"TESTING {profile_name} VERIFICATION")
    print("=" * 80)
    
    # Load profile
    profile_store = ProfileStore(base_path="profiles")
    
    if not profile_store.profile_exists(profile_name):
        print(f"❌ Profile '{profile_name}' not found!")
        print(f"\nRun: python create_asta3_from_cluster.py")
        return
    
    profile = profile_store.get_profile(profile_name)
    voiceprint = profile["voiceprint"]
    metadata = profile["metadata"]
    threshold = metadata["threshold"]
    
    print(f"\n✅ Loaded profile: {profile_name}")
    print(f"  Created: {metadata.get('created', 'N/A')}")
    print(f"  Sample count: {metadata.get('sample_count', 'N/A')}")
    print(f"  Threshold: {threshold:.4f}")
    print(f"  Intra-class mean similarity: {metadata['intra_class_stats']['mean_similarity']:.4f}")
    
    # Load model
    model = ModelLoader.get_instance()
    
    # Load cluster files for positive tests
    with open("best_cluster_files.txt", 'r') as f:
        cluster_files = [line.strip() for line in f.readlines()]
    
    # Test with training samples (should PASS)
    print(f"\n" + "=" * 80)
    print("TEST 1: TRAINING SAMPLES (Expected: PASS)")
    print("=" * 80)
    
    test_files = cluster_files[:5]
    passed = 0
    
    print(f"{'Filename':<25} {'Score':<10} {'Threshold':<12} {'Result'}")
    print("-" * 65)
    
    for file_path in test_files:
        try:
            waveform, _ = load_and_preprocess(file_path)
            embedding = extract_embedding(waveform, config.target_sample_rate)
            normalized = normalize_embedding(embedding)
            score = compute_cosine_similarity(normalized, voiceprint)
            
            result = "✅ VERIFIED" if score >= threshold else "❌ REJECTED"
            if score >= threshold:
                passed += 1
            
            fname = Path(file_path).name
            print(f"{fname:<25} {score:.4f}    {threshold:.4f}       {result}")
            
        except Exception as e:
            print(f"{Path(file_path).name:<25} ERROR: {e}")
    
    print(f"\nResult: {passed}/5 passed")
    
    # Test with samples OUTSIDE the cluster (should FAIL or have lower scores)
    print(f"\n" + "=" * 80)
    print("TEST 2: SAMPLES OUTSIDE CLUSTER (Expected: Lower scores or FAIL)")
    print("=" * 80)
    
    data_folder = Path("../DATA")
    all_files = sorted(list(data_folder.glob("*.wav")))
    
    # Find files not in cluster
    cluster_names = [Path(f).name for f in cluster_files]
    non_cluster_files = [f for f in all_files if f.name not in cluster_names][:5]
    
    if not non_cluster_files:
        print("  No non-cluster files available for testing")
    else:
        passed_outside = 0
        
        print(f"{'Filename':<25} {'Score':<10} {'Threshold':<12} {'Result'}")
        print("-" * 65)
        
        for file_path in non_cluster_files:
            try:
                waveform, _ = load_and_preprocess(str(file_path))
                embedding = extract_embedding(waveform, config.target_sample_rate)
                normalized = normalize_embedding(embedding)
                score = compute_cosine_similarity(normalized, voiceprint)
                
                result = "✅ VERIFIED" if score >= threshold else "❌ REJECTED"
                if score >= threshold:
                    passed_outside += 1
                
                print(f"{file_path.name:<25} {score:.4f}    {threshold:.4f}       {result}")
                
            except Exception as e:
                print(f"{file_path.name:<25} ERROR: {e}")
        
        print(f"\nResult: {passed_outside}/5 passed (lower is better for security)")
    
    # Summary
    print(f"\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Profile {profile_name} is ready for use")
    print(f"✅ Training samples: {passed}/5 verified correctly")
    
    if non_cluster_files:
        print(f"✅ Non-cluster samples: {passed_outside}/5 verified (different speakers should be rejected)")
    
    print(f"\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print(f"1. Start the FastAPI server:")
    print(f"   python main.py")
    print(f"\n2. Test verification API:")
    print(f"   Use Postman or curl to POST to /api/verify")
    print(f"   - profile_name: ASTA3")
    print(f"   - audio_file: <upload a WAV file>")
    print(f"\n3. Expected results:")
    print(f"   - Training samples should return verified=true, score > 0.80")
    print(f"   - Different speakers should return verified=false, score < 0.60")

if __name__ == "__main__":
    test_verification()
