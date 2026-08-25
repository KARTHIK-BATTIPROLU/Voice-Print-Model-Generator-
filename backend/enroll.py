import os
import sys
import torch
import numpy as np
import pandas as pd
from profile_store import ProfileStore
from model import ModelLoader

_classifier = None

def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = ModelLoader.get_instance()
    return _classifier


def embed(path):
    clf = get_classifier()
    signal = clf.load_audio(path)
    return clf.encode_batch(signal.unsqueeze(0)).squeeze().detach().numpy()


def cosine(a, b):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def run(session_id):
    manifest_path = "manifest.csv"
    if not os.path.exists(manifest_path):
        print(f"Error: {manifest_path} not found.")
        return {"success": False, "error": "manifest.csv not found"}

    df = pd.read_csv(manifest_path)
    
    # Filter by session_id and speaker_id
    session_df = df[df.session_id == session_id]
    if session_df.empty:
        # If no session matching session_id, filter by speaker_id
        session_df = df[df.speaker_id == "ASTA_primary"]

    if session_df.empty:
        print(f"No samples found for session_id '{session_id}' or speaker 'ASTA_primary'.")
        return {"success": False, "error": "No matching samples found in manifest"}

    # Filter out REJECTED_QUALITY samples if status column exists
    if "status" in session_df.columns:
        session_df = session_df[session_df.status == "OK"]

    enroll_df = session_df[session_df.is_holdout == False]
    holdout_df = session_df[session_df.is_holdout == True]

    if enroll_df.empty:
        print("No enrollment samples available.")
        return {"success": False, "error": "No valid enrollment samples"}

    embeddings = {}
    for _, row in enroll_df.iterrows():
        sample_id = row.sample_id if "sample_id" in row else str(row.file_path)
        try:
            embeddings[sample_id] = embed(row.file_path)
        except Exception as e:
            print(f"Error embedding {row.file_path}: {e}")

    ids = list(embeddings.keys())
    if not ids:
        return {"success": False, "error": "Failed to extract embeddings"}

    # Self-consistency check: drop clips whose avg similarity to rest is > 1.5 std below mean
    if len(ids) > 1:
        sims = {i: np.mean([cosine(embeddings[i], embeddings[j]) for j in ids if j != i]) for i in ids}
        mean_sim, std_sim = np.mean(list(sims.values())), np.std(list(sims.values()))
        kept = [i for i in ids if sims[i] >= mean_sim - 1.5 * std_sim]
        dropped = [i for i in ids if i not in kept]
    else:
        kept = ids
        dropped = []
        mean_sim, std_sim = 1.0, 0.0

    print(f"Kept {len(kept)}/{len(ids)} clips. Dropped as inconsistent: {dropped}")

    master = np.mean([embeddings[i] for i in kept], axis=0)
    master = master / np.linalg.norm(master) # Normalize master vector
    np.save("enrolled_voiceprint.npy", master)

    # Save to ProfileStore as 'ASTA_primary'
    try:
        store = ProfileStore(base_path="profiles")
        metadata = {
            "created": pd.Timestamp.now().isoformat(),
            "sample_count": len(kept),
            "dropped_count": len(dropped),
            "threshold": 0.65,
            "intra_class_stats": {
                "mean_similarity": float(mean_sim),
                "std_similarity": float(std_sim)
            },
            "session_id": session_id
        }
        if store.profile_exists("ASTA_primary"):
            store.delete_profile("ASTA_primary")
        store.create_profile("ASTA_primary", master, metadata)
        print("Profile 'ASTA_primary' saved to ProfileStore.")
    except Exception as e:
        print(f"Warning: Could not update ProfileStore: {e}")

    # Verification against holdout clips
    holdout_results = []
    for _, row in holdout_df.iterrows():
        sample_id = row.sample_id if "sample_id" in row else str(row.file_path)
        try:
            sample_emb = embed(row.file_path)
            score = cosine(sample_emb, master)
            passed = score >= 0.65
            status_str = "PASS" if passed else "BELOW THRESHOLD"
            print(f"Holdout {sample_id}: similarity={score:.3f} ({status_str})")
            holdout_results.append({
                "sample_id": sample_id,
                "score": float(score),
                "passed": passed,
                "status": status_str
            })
        except Exception as e:
            print(f"Error evaluating holdout {sample_id}: {e}")

    return {
        "success": True,
        "session_id": session_id,
        "kept_count": len(kept),
        "total_count": len(ids),
        "dropped": dropped,
        "mean_similarity": float(mean_sim),
        "std_similarity": float(std_sim),
        "holdout_results": holdout_results
    }


if __name__ == "__main__":
    sid = sys.argv[1] if len(sys.argv) > 1 else "default_session"
    run(sid)
