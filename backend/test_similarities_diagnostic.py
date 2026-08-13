import os
import sys
import torch
import numpy as np

# Add backend dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio_utils import load_and_preprocess
from embedding import extract_embedding, normalize_embedding, compute_cosine_similarity
from model import ModelLoader

def main():
    print("Running voiceprint diagnostics...")
    
    # Load model
    model = ModelLoader.get_instance()
    
    # Files
    file_7 = "c:/Users/Karthik/OneDrive/Desktop/Voice Print Model Generator/DATA/sample_0007.wav"
    file_8 = "c:/Users/Karthik/OneDrive/Desktop/Voice Print Model Generator/DATA/sample_0008.wav"
    file_9 = "c:/Users/Karthik/OneDrive/Desktop/Voice Print Model Generator/DATA/sample_0009.wav"
    
    print(f"Loading {file_7}...")
    w7, m7 = load_and_preprocess(file_7)
    e7 = normalize_embedding(extract_embedding(w7, 16000))
    
    print(f"Loading {file_8}...")
    w8, m8 = load_and_preprocess(file_8)
    e8 = normalize_embedding(extract_embedding(w8, 16000))
    
    print(f"Loading {file_9}...")
    w9, m9 = load_and_preprocess(file_9)
    e9 = normalize_embedding(extract_embedding(w9, 16000))
    
    # 1. Self similarity
    sim_7_7 = compute_cosine_similarity(e7, e7)
    print(f"Similarity of sample_0007.wav to itself: {sim_7_7:.6f} (Expected: 1.000000)")
    
    # 2. Pairwise similarity
    sim_7_8 = compute_cosine_similarity(e7, e8)
    sim_7_9 = compute_cosine_similarity(e7, e9)
    sim_8_9 = compute_cosine_similarity(e8, e9)
    print(f"Similarity of sample_0007 to sample_0008: {sim_7_8:.6f}")
    print(f"Similarity of sample_0007 to sample_0009: {sim_7_9:.6f}")
    print(f"Similarity of sample_0008 to sample_0009: {sim_8_9:.6f}")
    
    # 3. Average of these three
    avg_3 = normalize_embedding((e7 + e8 + e9) / 3.0)
    sim_7_avg = compute_cosine_similarity(e7, avg_3)
    sim_8_avg = compute_cosine_similarity(e8, avg_3)
    sim_9_avg = compute_cosine_similarity(e9, avg_3)
    print(f"Similarity of sample_0007 to average of the three: {sim_7_avg:.6f}")
    print(f"Similarity of sample_0008 to average of the three: {sim_8_avg:.6f}")
    print(f"Similarity of sample_0009 to average of the three: {sim_9_avg:.6f}")

if __name__ == "__main__":
    main()
