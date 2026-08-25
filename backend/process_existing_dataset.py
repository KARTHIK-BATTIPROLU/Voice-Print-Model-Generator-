import os
import glob
import torch
import sounddevice as sd
import numpy as np
import pandas as pd
from datetime import datetime
from audio_utils import load_and_preprocess
import enroll
from main import SCRIPTED_PHRASES, compute_audio_quality, append_to_manifest

def process_dataset():
    data_dir = "DATA"
    wav_files = sorted(glob.glob(os.path.join(data_dir, "sample_*.wav")))
    print(f"Found {len(wav_files)} WAV files in '{data_dir}'.")
    if not wav_files:
        print("No WAV files found in DATA directory.")
        return

    session_id = "dataset_enrollment_001"
    speaker_id = "ASTA_primary"
    room_tag = "user-dataset-room"

    try:
        device_info = sd.query_devices(kind='input')
        device_name = device_info.get('name', 'Default Input Device')
    except Exception:
        device_name = "Default Input Device"

    print(f"Processing {len(wav_files)} samples for session '{session_id}'...")

    # Clear manifest if previous test records existed for dataset_enrollment_001
    manifest_path = "manifest.csv"
    if os.path.exists(manifest_path):
        df = pd.read_csv(manifest_path)
        df = df[df.session_id != session_id]
        df.to_csv(manifest_path, index=False)

    total_files = len(wav_files)
    for idx, filepath in enumerate(wav_files):
        phrase_num = idx + 1
        phrase_index = idx % len(SCRIPTED_PHRASES)
        phrase_text = SCRIPTED_PHRASES[phrase_index]
        
        # If 20 samples, mark samples 1-18 as enrollment (False) and samples 19-20 as holdout (True)
        is_holdout = (idx >= 18) if total_files == 20 else (idx >= 20)

        try:
            waveform, meta = load_and_preprocess(filepath)
            rms_db, peak = compute_audio_quality(waveform)
            
            # Check quality
            status = "OK"
            sample_id = f"sample_{session_id}_{phrase_num:04d}"
            
            append_to_manifest({
                "sample_id": sample_id,
                "session_id": session_id,
                "speaker_id": speaker_id,
                "device_name": device_name,
                "room_tag": room_tag,
                "file_path": filepath,
                "phrase_index": phrase_num,
                "phrase_text": phrase_text,
                "is_holdout": is_holdout,
                "rms_db": round(rms_db, 2),
                "peak_amplitude": round(peak, 4),
                "status": status,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            print(f"[{idx+1}/{total_files}] Processed {os.path.basename(filepath)}: RMS={rms_db:.1f}dB, Peak={peak:.2f}, Holdout={is_holdout}")
        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    print("\nRunning post-session enrollment check and model creation...")
    res = enroll.run(session_id)
    print("\n--- ENROLLMENT RESULT ---")
    print(res)

if __name__ == "__main__":
    process_dataset()
