"""
End-to-end verification test for ASTA3 profile.
Run with: py test_verify.py
"""
import requests
import json
import struct
import math
import io
import os
import sys

BASE   = "http://localhost:8000"
FOLDER = r"C:\Dev\VoicePrintModel\data\samples\ASTA3"

# ── helper ────────────────────────────────────────────────────────────────────
def make_wav_bytes(freqs, sr=16000, secs=3):
    """Generate a WAV in memory with given harmonic frequencies."""
    n   = sr * secs
    raw = []
    for i in range(n):
        t = i / sr
        v = sum(math.sin(2*math.pi*f*t) * (1.0/(idx+1))
                for idx, f in enumerate(freqs))
        raw.append(max(-32767, min(32767, int(v / (len(freqs)+0.5) * 32767))))
    data = struct.pack("<" + "h"*n, *raw)
    hdr  = (b"RIFF" + struct.pack("<I", 36+len(data)) + b"WAVEfmt "
            + struct.pack("<IHHIIHH", 16, 1, 1, sr, sr*2, 2, 16)
            + b"data" + struct.pack("<I", len(data)))
    return hdr + data

# ── TEST 1: same samples must MATCH ──────────────────────────────────────────
print("=" * 60)
print("  TEST 1: Enroll samples → should all MATCH ASTA3")
print("=" * 60)

files = sorted([f for f in os.listdir(FOLDER) if f.endswith(".wav")])
passed = 0
for fname in files:
    with open(os.path.join(FOLDER, fname), "rb") as fh:
        r = requests.post(
            f"{BASE}/api/verify",
            data={"profile_name": "ASTA3"},
            files={"audio": (fname, fh, "audio/wav")},
            timeout=30,
        )
    d = r.json()
    ok   = d.get("verified", False)
    icon = "✅ MATCH   " if ok else "❌ NO MATCH"
    print(f"  {icon}  {fname}  "
          f"score={d.get('similarity_score',0):.4f}  "
          f"thresh={d.get('threshold',0):.2f}")
    if ok:
        passed += 1

print(f"\n  Passed: {passed}/{len(files)}")

# ── TEST 2: different audio should NOT match ──────────────────────────────────
print("\n" + "=" * 60)
print("  TEST 2: Different audio → should NOT match ASTA3")
print("=" * 60)

different = make_wav_bytes([800.0, 1600.0, 2400.0])   # completely different timbre
r = requests.post(
    f"{BASE}/api/verify",
    data={"profile_name": "ASTA3"},
    files={"audio": ("stranger.wav", io.BytesIO(different), "audio/wav")},
    timeout=30,
)
d = r.json()
ok   = not d.get("verified", True)   # expect NO MATCH
icon = "✅ NO MATCH (correct)" if ok else "❌ FALSE ACCEPT (wrong!)"
print(f"  {icon}  score={d.get('similarity_score',0):.4f}  "
      f"thresh={d.get('threshold',0):.2f}")

# ── SUMMARY ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
all_ok = (passed == len(files)) and ok
print("  OVERALL RESULT:", "✅ ALL TESTS PASSED" if all_ok else "❌ SOME TESTS FAILED")
print("=" * 60)
sys.exit(0 if all_ok else 1)
