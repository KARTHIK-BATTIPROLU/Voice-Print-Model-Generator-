"""Quick diagnostic script to check DATA folder audio properties"""
import torchaudio
from pathlib import Path
import numpy as np

data_folder = Path("../DATA")
wav_files = list(data_folder.glob("*.wav"))[:10]

print(f"=== AUDIO DATA AUDIT ===")
print(f"Total files found: {len(list(data_folder.glob('*.wav')))}")
print(f"Checking first 10 samples:\n")

sample_rates = {}
durations = []
channels_list = []
too_short = []
corrupt = []

for wav_path in wav_files:
    try:
        waveform, sr = torchaudio.load(str(wav_path))
        num_channels = waveform.shape[0]
        num_samples = waveform.shape[1]
        duration = num_samples / sr
        
        sample_rates[sr] = sample_rates.get(sr, 0) + 1
        durations.append(duration)
        channels_list.append(num_channels)
        
        print(f"{wav_path.name}:")
        print(f"  Sample Rate: {sr} Hz")
        print(f"  Channels: {num_channels} ({'mono' if num_channels == 1 else 'stereo'})")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Samples: {num_samples}")
        
        if duration < 1.5:
            too_short.append(wav_path.name)
            print(f"  ⚠️ TOO SHORT (< 1.5s)")
        
        print()
        
    except Exception as e:
        corrupt.append((wav_path.name, str(e)))
        print(f"{wav_path.name}: ❌ CORRUPT - {e}\n")

print("\n=== SUMMARY ===")
print(f"Sample rate distribution: {sample_rates}")
print(f"Duration range: {min(durations):.2f}s - {max(durations):.2f}s")
mono_count = sum(1 for c in channels_list if c == 1)
stereo_count = sum(1 for c in channels_list if c > 1)
print(f"Mono: {mono_count}, Stereo: {stereo_count}")
print(f"Too short (< 1.5s): {len(too_short)}")
if too_short:
    print(f"  Files: {too_short}")
print(f"Corrupt files: {len(corrupt)}")
if corrupt:
    for name, err in corrupt:
        print(f"  {name}: {err}")

print("\n=== CRITICAL CHECKS ===")
if len(sample_rates) > 1:
    print("⚠️ MULTIPLE SAMPLE RATES DETECTED - resampling needed!")
else:
    sr = list(sample_rates.keys())[0]
    if sr != 16000:
        print(f"⚠️ Sample rate is {sr} Hz, not 16000 Hz - resampling needed!")
    else:
        print("✅ All files are 16 kHz")
        
if stereo_count > 0:
    print(f"⚠️ {stereo_count} stereo files detected - mono conversion needed!")
else:
    print("✅ All files are mono")
