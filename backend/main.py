"""
FastAPI application — VoicePrint enrollment & verification API.
"""
import os
import io
import time
import logging
import tempfile

import numpy as np
import torch
import torchaudio
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import config
import embedding as emb_engine
import profile_store as store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── App setup ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="VoicePrint API",
    description="Voice biometric enrollment and verification API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

startup_time: float = 0.0


@app.on_event("startup")
async def on_startup():
    global startup_time
    startup_time = time.time()
    logger.info("VoicePrint API started")


# ─── helpers ─────────────────────────────────────────────────────────────────

def _load_audio_bytes(data: bytes, filename: str = "audio") -> tuple[torch.Tensor, int]:
    """
    Load audio from raw bytes. Supports WAV, WebM, OGG, MP3, FLAC.
    Returns (waveform [1, samples], sample_rate).
    """
    suffix = os.path.splitext(filename)[-1].lower() or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        waveform, sr = torchaudio.load(tmp_path)
    except Exception:
        # torchaudio couldn't load (e.g. webm) — try soundfile via io.BytesIO
        try:
            import soundfile as sf
            sig, sr = sf.read(io.BytesIO(data))
            if sig.ndim == 1:
                sig = sig[np.newaxis, :]
            else:
                sig = sig.T
            waveform = torch.from_numpy(sig.astype(np.float32))
        except Exception as e2:
            os.unlink(tmp_path)
            raise ValueError(f"Cannot decode audio: {e2}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    # Ensure float32
    if waveform.dtype != torch.float32:
        waveform = waveform.float()

    return waveform, sr


def _preprocess(waveform: torch.Tensor, sr: int) -> torch.Tensor:
    """
    Convert to mono → resample to 16 kHz → normalize amplitude.
    """
    # mono
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    # resample
    target_sr = config.target_sample_rate   # 16000
    if sr != target_sr:
        waveform = torchaudio.functional.resample(waveform, sr, target_sr)

    # normalize
    max_val = waveform.abs().max()
    if max_val > 1e-6:
        waveform = waveform / max_val

    return waveform                         # shape (1, N)


def _audio_from_upload(upload: UploadFile) -> torch.Tensor:
    """Read upload → preprocess → return waveform tensor (1, N) at 16kHz."""
    raw = upload.file.read()
    waveform, sr = _load_audio_bytes(raw, upload.filename or "audio.wav")
    return _preprocess(waveform, sr)


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"service": "VoicePrint API", "version": "1.0.0", "status": "online"}


@app.get("/api/health")
async def health():
    uptime = time.time() - startup_time
    return {
        "status":        "healthy",
        "model_loaded":  emb_engine._encoder is not None,
        "profile_count": store.count_profiles(),
        "uptime":        uptime,
    }


# ── GET /api/profiles ────────────────────────────────────────────────────────
@app.get("/api/profiles")
async def get_profiles():
    """Return all enrolled speaker profiles (no voiceprint vectors)."""
    return store.list_profiles()


# ── GET /api/profiles/{name} ─────────────────────────────────────────────────
@app.get("/api/profiles/{name}")
async def get_profile(name: str):
    profile = store.load_profile(name)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")
    profile.pop("voiceprint", None)         # don't send binary blob as JSON
    return profile


# ── POST /api/enroll ─────────────────────────────────────────────────────────
@app.post("/api/enroll")
async def enroll(
    name:  str        = Form(...),
    audio: UploadFile = File(...),
):
    """
    Enroll a speaker from a single audio file.
    Extracts an ECAPA-TDNN / MFCC embedding, saves as a voice profile.
    """
    if not name.strip():
        raise HTTPException(status_code=422, detail="Speaker name cannot be empty")

    name = name.strip()
    logger.info(f"Enrolling '{name}' from file '{audio.filename}'")

    try:
        waveform = _audio_from_upload(audio)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Check minimum duration (1.5 s at 16 kHz = 24000 samples)
    min_samples = int(config.min_duration_sec * config.target_sample_rate)
    if waveform.shape[-1] < min_samples:
        raise HTTPException(
            status_code=422,
            detail=f"Audio too short ({waveform.shape[-1]/config.target_sample_rate:.2f}s); "
                   f"minimum is {config.min_duration_sec}s",
        )

    # Extract + normalize embedding
    raw_emb  = emb_engine.extract_embedding(waveform)
    norm_emb = emb_engine.normalize_embedding(raw_emb)

    stats     = emb_engine.compute_intra_class_stats([norm_emb])
    threshold = stats["suggested_threshold"]

    # If profile already exists, average with existing voiceprint
    existing  = store.load_profile(name)
    if existing is not None:
        old_vp    = existing["voiceprint"]
        old_count = existing["sample_count"]
        # weighted average
        combined  = (old_vp * old_count + norm_emb) / (old_count + 1)
        voiceprint = emb_engine.normalize_embedding(combined)
        sample_count = old_count + 1
    else:
        voiceprint   = norm_emb
        sample_count = 1

    meta = store.save_profile(
        name         = name,
        voiceprint   = voiceprint,
        sample_count = sample_count,
        threshold    = threshold,
        intra_class_stats = stats,
    )

    return {
        "success":      True,
        "name":         name,
        "sample_count": sample_count,
        "threshold":    threshold,
        "message":      f"Speaker '{name}' enrolled successfully",
    }


# ── POST /api/enroll/batch ────────────────────────────────────────────────────
@app.post("/api/enroll/batch")
async def enroll_batch(
    name:   str             = Form(...),
    audios: list[UploadFile] = File(...),
):
    """
    Enroll from multiple audio files at once.
    Averages embeddings from all files into one voiceprint.
    """
    if not name.strip():
        raise HTTPException(status_code=422, detail="Speaker name cannot be empty")
    name = name.strip()

    embeddings = []
    for upload in audios:
        try:
            waveform = _audio_from_upload(upload)
            raw_emb  = emb_engine.extract_embedding(waveform)
            embeddings.append(emb_engine.normalize_embedding(raw_emb))
        except Exception as e:
            logger.warning(f"Skipping {upload.filename}: {e}")

    if not embeddings:
        raise HTTPException(status_code=422, detail="No valid audio files provided")

    # Outlier filtering
    keep_flags  = emb_engine.detect_outliers(embeddings)
    clean_embs  = [e for e, k in zip(embeddings, keep_flags) if k]
    if not clean_embs:
        clean_embs = embeddings

    voiceprint = emb_engine.average_embeddings(clean_embs)
    stats      = emb_engine.compute_intra_class_stats(clean_embs)
    # When all samples are near-identical (std≈0), use a safe fixed threshold
    threshold  = stats["suggested_threshold"] if stats["std_similarity"] > 0.001 else 0.75

    meta = store.save_profile(
        name              = name,
        voiceprint        = voiceprint,
        sample_count      = len(clean_embs),
        threshold         = threshold,
        intra_class_stats = stats,
    )

    return {
        "success":      True,
        "name":         name,
        "sample_count": len(clean_embs),
        "threshold":    threshold,
        "stats":        stats,
        "message":      f"Enrolled '{name}' from {len(clean_embs)} samples",
    }


# ── POST /api/verify ─────────────────────────────────────────────────────────
@app.post("/api/verify")
async def verify(
    profile_name: str        = Form(...),
    audio:        UploadFile = File(...),
):
    """
    Verify whether the audio matches the enrolled profile.
    Returns similarity score and MATCH / NO MATCH verdict.
    """
    profile = store.load_profile(profile_name)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{profile_name}' not found. Enroll first.",
        )

    try:
        waveform = _audio_from_upload(audio)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    min_samples = int(config.min_duration_sec * config.target_sample_rate)
    if waveform.shape[-1] < min_samples:
        raise HTTPException(
            status_code=422,
            detail=f"Audio too short ({waveform.shape[-1]/config.target_sample_rate:.2f}s)",
        )

    raw_emb  = emb_engine.extract_embedding(waveform)
    query    = emb_engine.normalize_embedding(raw_emb)
    stored   = profile["voiceprint"]                   # already normalized

    score     = emb_engine.compute_cosine_similarity(query, stored)
    threshold = profile.get("threshold", config.default_threshold)
    verified  = score >= threshold

    logger.info(
        f"Verify '{profile_name}': score={score:.4f} "
        f"thresh={threshold:.2f} → {'MATCH' if verified else 'NO MATCH'}"
    )

    return {
        "verified":         verified,
        "similarity_score": round(score, 4),
        "threshold":        threshold,
        "profile_name":     profile_name,
        "verdict":          "MATCH" if verified else "NO MATCH",
    }


# ── DELETE /api/profiles/{name} ──────────────────────────────────────────────
@app.delete("/api/profiles/{name}")
async def delete_profile(name: str):
    deleted = store.delete_profile(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")
    return {"success": True, "message": f"Profile '{name}' deleted"}


# ── PATCH /api/profiles/{name}/threshold ─────────────────────────────────────
@app.patch("/api/profiles/{name}/threshold")
async def update_threshold(name: str, threshold: float = Form(...)):
    if not (0.0 <= threshold <= 1.0):
        raise HTTPException(status_code=422, detail="Threshold must be between 0.0 and 1.0")
    updated = store.update_threshold(name, threshold)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")
    return {"success": True, "name": name, "threshold": threshold}


# ─── Dev entry point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.server.host, port=config.server.port, reload=True)
