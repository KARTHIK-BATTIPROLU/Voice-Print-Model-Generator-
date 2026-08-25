"""
FastAPI application entry point for VoicePrint system.
Validates: Requirements 6, 7, 8.2, 8.4, 8.8, 10, 11
"""
import time
import os
import re
import shutil
import tempfile
import json
import csv
import logging
from typing import Optional, List, Dict
from datetime import datetime

import numpy as np
import torch
try:
    import sounddevice as sd
except Exception:
    sd = None
from fastapi import FastAPI, File, UploadFile, Form, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware

from config import config
from model import ModelLoader
from profile_store import ProfileStore
from audio_utils import load_and_preprocess, convert_webm_to_wav
from embedding import (
    extract_embedding,
    normalize_embedding,
    average_embeddings,
    compute_cosine_similarity,
    detect_outliers,
    compute_intra_class_stats
)
import enroll

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Scripted phrases list for single-session enrollment
SCRIPTED_PHRASES = [
    "Asta, what's on my schedule today.",
    "Hey Asta, set a timer for ten minutes.",
    "Asta, three seven two nine one.",
    "This is just me talking normally for a few seconds.",
    "Asta, can you check the weather.",
    "One two three four five six seven.",
    "Asta, remind me to call back later.",
    "I'm recording this in one sitting on one device.",
    "Asta, play some music.",
    "Testing testing, this is sample number ten.",
    "Asta, what time is it right now.",
    "A quick brown fox jumps over something or other.",
    "Asta, stop.",
    "Nine eight seven six five four three.",
    "Asta, open my notes app.",
    "Just another casual sentence for variety.",
    "Asta, how's the traffic looking.",
    "Twelve, twenty, two hundred, two thousand.",
    "Asta, good morning.",
    "Last one, wrapping up the enrollment set.",
    "Asta, are you listening.",
    "This is a held-out test clip, not enrollment."
]

# Create FastAPI app instance
app = FastAPI(
    title="VoicePrint API",
    description="Voice biometric enrollment and verification API",
    version="1.0.0"
)

# Configure CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.server.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

# Track application startup time
startup_time = None

# Initialize ProfileStore
profile_store = ProfileStore(base_path=config.storage_path)

# Active WebSocket connections for progress tracking
active_websockets: Dict[str, WebSocket] = {}

# Active single enrollment session state
active_enrollment_session: Optional[Dict] = None



@app.on_event("startup")
async def startup_event():
    """Startup event handler - initialize resources"""
    global startup_time
    startup_time = time.time()
    logger.info("VoicePrint API starting up...")
    
    # Pre-load the singleton model to avoid timeout on first request
    try:
        logger.info("Pre-loading model...")
        ModelLoader.get_instance()
        logger.info("Model loaded successfully on startup.")
    except Exception as e:
        logger.error(f"Failed to load model on startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler - cleanup resources"""
    logger.info("VoicePrint API shutting down...")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "VoicePrint API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint - returns model status and uptime"""
    uptime = time.time() - startup_time if startup_time else 0.0
    model_ready = ModelLoader.is_loaded()
    
    try:
        profile_count = len(profile_store.list_profiles())
    except Exception:
        profile_count = 0
        
    return {
        "status": "healthy" if model_ready else "unhealthy",
        "model_loaded": model_ready,
        "profile_count": profile_count,
        "uptime": uptime
    }


@app.websocket("/ws/progress/{session_id}")
async def websocket_progress_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket connection for streaming enrollment progress"""
    await websocket.accept()
    active_websockets[session_id] = websocket
    logger.info(f"WebSocket client connected: {session_id}")
    try:
        while True:
            # Keep connection open, client might send heartbeats
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {session_id}")
    finally:
        active_websockets.pop(session_id, None)


async def send_ws_progress(session_id: Optional[str], current: int, total: int, message: str):
    """Helper to stream progress updates to the active WebSocket session"""
    if not session_id or session_id not in active_websockets:
        return
    ws = active_websockets[session_id]
    try:
        await ws.send_json({
            "type": "progress",
            "current": current,
            "total": total,
            "percentage": round((current / total) * 100, 1),
            "message": message
        })
    except Exception as e:
        logger.warning(f"Failed to send WS progress update: {e}")


async def send_ws_complete(session_id: Optional[str], success: bool, result: dict):
    """Helper to stream completion message to the active WebSocket session"""
    if not session_id or session_id not in active_websockets:
        return
    ws = active_websockets[session_id]
    try:
        await ws.send_json({
            "type": "complete",
            "success": success,
            "result": result
        })
    except Exception as e:
        logger.warning(f"Failed to send WS completion: {e}")


async def send_ws_quality_warning(session_id: Optional[str], reason: str, rms_db: float, peak: float, phrase_index: int):
    """Helper to stream quality warning updates to the active WebSocket session"""
    if not session_id or session_id not in active_websockets:
        return
    ws = active_websockets[session_id]
    try:
        await ws.send_json({
            "type": "quality_warning",
            "reason": reason,
            "rms_db": round(rms_db, 2),
            "peak": round(peak, 4),
            "phrase_index": phrase_index
        })
    except Exception as e:
        logger.warning(f"Failed to send WS quality warning: {e}")


def compute_audio_quality(waveform: torch.Tensor):
    """Computes audio RMS in dB and Peak Amplitude"""
    samples = waveform.squeeze().cpu().numpy()
    rms = float(np.sqrt(np.mean(samples ** 2)))
    rms_db = float(20.0 * np.log10(rms + 1e-9))
    peak = float(np.max(np.abs(samples)))
    return rms_db, peak


def append_to_manifest(row_dict: dict):
    """Appends a sample record to manifest.csv"""
    manifest_path = "manifest.csv"
    file_exists = os.path.exists(manifest_path)
    fieldnames = [
        "sample_id", "session_id", "speaker_id", "device_name", "room_tag",
        "file_path", "phrase_index", "phrase_text", "is_holdout",
        "rms_db", "peak_amplitude", "status", "timestamp"
    ]
    with open(manifest_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_dict)



@app.get("/api/profiles")
async def list_profiles_endpoint():
    """List all profiles with metadata summaries"""
    try:
        profiles = profile_store.list_profiles()
        return {"profiles": profiles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list profiles: {str(e)}")


@app.get("/api/profiles/{name}")
async def get_profile_endpoint(name: str):
    """Retrieve metadata for a specific profile"""
    if not profile_store._validate_profile_name(name):
        raise HTTPException(status_code=400, detail="Invalid profile name format")
        
    if not profile_store.profile_exists(name):
        return {"name": name, "exists": False, "metadata": {}}
        
    try:
        profile = profile_store.get_profile(name)
        if not profile:
            return {"name": name, "exists": False, "metadata": {}}
        return {
            "name": name,
            "exists": True,
            "metadata": profile["metadata"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@app.delete("/api/profiles/{name}")
async def delete_profile_endpoint(name: str):
    """Delete a profile and its associated files"""
    if not profile_store._validate_profile_name(name):
        raise HTTPException(status_code=400, detail="Invalid profile name format")
        
    if not profile_store.profile_exists(name):
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")
        
    try:
        deleted = profile_store.delete_profile(name)
        return {"success": deleted, "deleted": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete profile: {str(e)}")


@app.patch("/api/profiles/{name}/threshold")
async def update_threshold_endpoint(name: str, payload: Dict[str, float] = Body(...)):
    """Update profile-specific similarity threshold"""
    if not profile_store._validate_profile_name(name):
        raise HTTPException(status_code=400, detail="Invalid profile name format")
        
    if not profile_store.profile_exists(name):
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")
        
    threshold = payload.get("threshold")
    if threshold is None or not (0.0 <= threshold <= 1.0):
        raise HTTPException(status_code=400, detail="Threshold must be in range [0.0, 1.0]")
        
    try:
        updated = profile_store.update_threshold(name, threshold)
        return {"success": updated, "updated": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update threshold: {str(e)}")


@app.post("/api/enroll")
async def enroll_profile_endpoint(
    profile_name: str = Form(...),
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Enroll a new profile with voice samples.
    Validates files, processes audio, extracts and averages embeddings,
    and runs outlier quality checks.
    """
    # 1. Input validations
    if not profile_store._validate_profile_name(profile_name):
        raise HTTPException(status_code=400, detail=f"Invalid profile name format. Name must be 1-64 chars of alphanumeric, dashes, or underscores.")
        
    if profile_store.profile_exists(profile_name):
        raise HTTPException(status_code=400, detail=f"Profile '{profile_name}' already exists.")
        
    min_s = config.enrollment.min_samples
    max_s = config.enrollment.max_samples
    if len(files) < min_s or len(files) > max_s:
        raise HTTPException(status_code=400, detail=f"Enrollment requires between {min_s} and {max_s} files, got {len(files)}.")

    # 2. Make temporary directory for conversion and preprocessing
    temp_dir = tempfile.mkdtemp(prefix=f"enroll_{profile_name}_")
    
    try:
        valid_embeddings = []
        rejected_count = 0
        total_files = len(files)
        
        await send_ws_progress(session_id, 0, total_files, "Starting enrollment processing...")
        
        for idx, upload_file in enumerate(files):
            # Save upload file
            file_ext = os.path.splitext(upload_file.filename)[1].lower()
            temp_input_path = os.path.join(temp_dir, f"raw_{idx}{file_ext}")
            
            with open(temp_input_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
                
            processed_wav_path = temp_input_path
            
            # Convert WebM or other formats to WAV if needed
            is_wav = False
            try:
                with open(temp_input_path, "rb") as f:
                    header = f.read(4)
                is_wav = header == b"RIFF"
            except Exception:
                pass

            if not is_wav or file_ext != ".wav":
                processed_wav_path = os.path.join(temp_dir, f"converted_{idx}.wav")
                try:
                    await send_ws_progress(session_id, idx, total_files, f"Converting {upload_file.filename} to WAV...")
                    convert_webm_to_wav(temp_input_path, processed_wav_path)
                except Exception as e:
                    logger.warning(f"Failed to convert file {upload_file.filename}: {e}")
                    rejected_count += 1
                    continue
            
            # Preprocess and load waveform
            try:
                await send_ws_progress(session_id, idx, total_files, f"Preprocessing {upload_file.filename}...")
                waveform, meta = load_and_preprocess(processed_wav_path)
            except Exception as e:
                logger.warning(f"Failed to preprocess file {upload_file.filename}: {e}")
                rejected_count += 1
                continue
                
            # Extract and L2-normalize embedding
            try:
                await send_ws_progress(session_id, idx, total_files, f"Extracting embedding for {upload_file.filename}...")
                embedding = extract_embedding(waveform, config.target_sample_rate)
                normalized = normalize_embedding(embedding)
                valid_embeddings.append(normalized)
            except Exception as e:
                logger.error(f"Failed to extract embedding for {upload_file.filename}: {e}")
                rejected_count += 1
                continue
                
            # Send progress update
            await send_ws_progress(session_id, idx + 1, total_files, f"Processed {idx + 1}/{total_files} samples")

        # 3. Final sample size verification
        if len(valid_embeddings) < min_s:
            error_msg = f"Failed to enroll: Only {len(valid_embeddings)} of {total_files} samples were valid (minimum {min_s} required)."
            result = {"success": False, "error": error_msg}
            await send_ws_complete(session_id, False, result)
            raise HTTPException(status_code=400, detail=error_msg)
            
        # 4. Outlier detection
        await send_ws_progress(session_id, total_files, total_files, "Computing quality metrics and outliers...")
        outlier_indices = detect_outliers(valid_embeddings, threshold=config.enrollment.outlier_threshold)
        
        # Filter outliers for average embedding
        clean_embeddings = [emb for i, emb in enumerate(valid_embeddings) if i not in outlier_indices]
        if not clean_embeddings:
            clean_embeddings = valid_embeddings
            
        # Average & L2 normalize
        voiceprint = average_embeddings(clean_embeddings)
        voiceprint = normalize_embedding(voiceprint)
        
        # Compute intra-class statistics
        stats = compute_intra_class_stats(valid_embeddings)
        
        # Save profile
        metadata = {
            "created": datetime.utcnow().isoformat() + "Z",
            "sample_count": len(valid_embeddings),
            "threshold": config.default_threshold,
            "intra_class_stats": stats,
            "outliers_detected": outlier_indices,
            "last_verified": None,
            "version": "1.0"
        }
        
        profile_store.create_profile(profile_name, voiceprint, metadata)
        
        result_payload = {
            "success": True,
            "profile_name": profile_name,
            "voiceprint_created": True,
            "samples_processed": len(valid_embeddings),
            "samples_rejected": rejected_count,
            "outliers_detected": outlier_indices,
            "intra_class_stats": stats,
            "error": None
        }
        
        await send_ws_complete(session_id, True, result_payload)
        return result_payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enrollment failure: {e}")
        result_payload = {"success": False, "error": str(e)}
        await send_ws_complete(session_id, False, result_payload)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/verify")
async def verify_endpoint(
    profile_name: str = Form(...),
    audio_file: UploadFile = File(...)
):
    """Verify a single audio file against an enrolled profile"""
    if not profile_store._validate_profile_name(profile_name):
        raise HTTPException(status_code=400, detail="Invalid profile name format")
        
    if not profile_store.profile_exists(profile_name):
        raise HTTPException(status_code=404, detail=f"Profile '{profile_name}' not found")
        
    temp_dir = tempfile.mkdtemp(prefix=f"verify_{profile_name}_")
    try:
        # Save upload file
        file_ext = os.path.splitext(audio_file.filename)[1].lower()
        temp_input_path = os.path.join(temp_dir, f"raw{file_ext}")
        with open(temp_input_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
            
        processed_wav_path = temp_input_path
        
        # Convert WebM to WAV if needed
        is_wav = False
        try:
            with open(temp_input_path, "rb") as f:
                header = f.read(4)
            is_wav = header == b"RIFF"
        except Exception:
            pass

        if not is_wav or file_ext != ".wav":
            processed_wav_path = os.path.join(temp_dir, "converted.wav")
            convert_webm_to_wav(temp_input_path, processed_wav_path)
            
        # Preprocess WAV
        waveform, meta = load_and_preprocess(processed_wav_path)
        
        # Extract embedding and normalize
        embedding = extract_embedding(waveform, config.target_sample_rate)
        normalized_emb = normalize_embedding(embedding)
        
        # Load profile
        profile = profile_store.get_profile(profile_name)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_name}' data not found")
            
        voiceprint = profile["voiceprint"]
        profile_meta = profile["metadata"]
        threshold = profile_meta.get("threshold", config.default_threshold)
        
        # Compute cosine similarity
        similarity = compute_cosine_similarity(normalized_emb, voiceprint)
        verified = similarity >= threshold
        
        # Update last verified timestamp in metadata
        profile_meta["last_verified"] = datetime.utcnow().isoformat() + "Z"
        profile_store.update_threshold(profile_name, threshold) # Save by updating threshold (re-saves metadata)
        
        # Overwrite metadata file directly to save last_verified
        meta_path = profile_store._get_metadata_path(profile_name)
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(profile_meta, f, indent=2)
            
        return {
            "success": True,
            "profile_name": profile_name,
            "similarity_score": similarity,
            "threshold": threshold,
            "verified": verified,
            "error": None
        }
        
    except ValueError as ve:
        # Catch preprocessing errors (e.g. SNR too low)
        logger.warning(f"Verification preprocessing error: {ve}")
        return {
            "success": False,
            "profile_name": profile_name,
            "similarity_score": 0.0,
            "threshold": 0.0,
            "verified": False,
            "error": str(ve)
        }
    except Exception as e:
        logger.error(f"Verification failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/verify/batch")
async def verify_batch_endpoint(
    profile_name: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Verify multiple files against a profile and return batch summary stats"""
    if not profile_store._validate_profile_name(profile_name):
        raise HTTPException(status_code=400, detail="Invalid profile name format")
        
    if not profile_store.profile_exists(profile_name):
        raise HTTPException(status_code=404, detail=f"Profile '{profile_name}' not found")
        
    # Load profile
    profile = profile_store.get_profile(profile_name)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_name}' data not found")
        
    voiceprint = profile["voiceprint"]
    profile_meta = profile["metadata"]
    threshold = profile_meta.get("threshold", config.default_threshold)
    
    temp_dir = tempfile.mkdtemp(prefix=f"verify_batch_{profile_name}_")
    results = []
    
    try:
        for upload_file in files:
            file_ext = os.path.splitext(upload_file.filename)[1].lower()
            temp_input_path = os.path.join(temp_dir, f"raw_{len(results)}{file_ext}")
            
            with open(temp_input_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
                
            processed_wav_path = temp_input_path
            
            try:
                # Convert WebM to WAV if needed
                is_wav = False
                try:
                    with open(temp_input_path, "rb") as f:
                        header = f.read(4)
                    is_wav = header == b"RIFF"
                except Exception:
                    pass

                if not is_wav or file_ext != ".wav":
                    processed_wav_path = os.path.join(temp_dir, f"converted_{len(results)}.wav")
                    convert_webm_to_wav(temp_input_path, processed_wav_path)
                    
                # Preprocess WAV
                waveform, meta = load_and_preprocess(processed_wav_path)
                
                # Extract embedding
                embedding = extract_embedding(waveform, config.target_sample_rate)
                normalized_emb = normalize_embedding(embedding)
                
                # Similarity
                similarity = compute_cosine_similarity(normalized_emb, voiceprint)
                verified = similarity >= threshold
                
                results.append({
                    "filename": upload_file.filename,
                    "similarity_score": similarity,
                    "verified": verified,
                    "error": None
                })
            except Exception as e:
                logger.warning(f"Batch verify failed for file {upload_file.filename}: {e}")
                results.append({
                    "filename": upload_file.filename,
                    "similarity_score": 0.0,
                    "verified": False,
                    "error": str(e)
                })
                
        # Calculate summary statistics
        valid_scores = [r["similarity_score"] for r in results if r["error"] is None]
        passed_count = sum(1 for r in results if r["verified"])
        
        summary = {
            "total_files": len(files),
            "passed_files": passed_count,
            "failed_files": len(files) - passed_count,
            "pass_rate": passed_count / len(files) if files else 0.0,
            "mean_score": float(np.mean(valid_scores)) if valid_scores else 0.0,
            "std_score": float(np.std(valid_scores)) if valid_scores else 0.0
        }
        
        return {
            "success": True,
            "profile_name": profile_name,
            "results": results,
            "summary": summary,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Batch verification failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ==========================================
# Single-Session Enrollment Endpoints
# ==========================================

@app.post("/api/session/start")
async def start_session_endpoint(
    room_tag: str = Form("bedroom-laptop-mic"),
    speaker_id: Optional[str] = Form(None)
):
    """
    Start a new single-speaker enrollment session.
    Enforces single_session_lock: returns HTTP 409 if an active session exists.
    Captures input device provenance and room_tag.
    """
    global active_enrollment_session

    if config.enrollment.single_session_lock and active_enrollment_session:
        if active_enrollment_session.get("status") == "ACTIVE":
            raise HTTPException(
                status_code=409,
                detail="An active enrollment session already exists. Finalize or reset it before starting a new one."
            )

    # Capture input device name via sounddevice
    device_name = "Default Input Device"
    if sd is not None:
        try:
            device_info = sd.query_devices(kind='input')
            device_name = device_info.get('name', 'Default Input Device')
        except Exception:
            pass

    session_id = f"session_{int(time.time())}"
    target_speaker = speaker_id or config.enrollment.speaker_id

    active_enrollment_session = {
        "session_id": session_id,
        "speaker_id": target_speaker,
        "device_name": device_name,
        "room_tag": room_tag,
        "status": "ACTIVE",
        "start_time": datetime.utcnow().isoformat() + "Z",
        "current_phrase_index": 0,
        "valid_clips": 0,
        "target_samples": config.enrollment.target_samples,
        "holdout_samples": config.enrollment.holdout_samples,
        "phrases": SCRIPTED_PHRASES
    }

    logger.info(f"Started enrollment session {session_id} for speaker '{target_speaker}' in room '{room_tag}' on device '{device_name}'")
    return {
        "success": True,
        "session": active_enrollment_session
    }


@app.get("/api/session/status")
async def get_session_status_endpoint():
    """Get active session status and provenance information"""
    if not active_enrollment_session:
        return {"active": False, "session": None}
    return {
        "active": True,
        "session": active_enrollment_session
    }


@app.post("/api/session/reset")
async def reset_session_endpoint():
    """Reset the active enrollment session lock"""
    global active_enrollment_session
    active_enrollment_session = None
    logger.info("Enrollment session reset")
    return {"success": True, "message": "Session reset successfully"}


@app.post("/api/session/clip")
async def process_session_clip_endpoint(
    session_id: str = Form(...),
    audio_file: UploadFile = File(...)
):
    """
    Process a single audio clip during an active enrollment session.
    Runs Quality Gate (RMS & Peak check).
    Logs clip to manifest.csv and streams WebSocket events.
    """
    global active_enrollment_session

    if not active_enrollment_session or active_enrollment_session.get("session_id") != session_id:
        raise HTTPException(status_code=400, detail="Invalid or inactive session ID")

    if active_enrollment_session.get("status") != "ACTIVE":
        raise HTTPException(status_code=400, detail="Session is already finalized or stopped")

    current_idx = active_enrollment_session["current_phrase_index"]
    phrases = active_enrollment_session["phrases"]
    if current_idx >= len(phrases):
        raise HTTPException(status_code=400, detail="All session phrases have already been recorded")

    phrase_text = phrases[current_idx]
    is_holdout = current_idx >= config.enrollment.target_samples

    temp_dir = tempfile.mkdtemp(prefix=f"clip_{session_id}_")
    try:
        file_ext = os.path.splitext(audio_file.filename)[1].lower()
        temp_input_path = os.path.join(temp_dir, f"raw_{current_idx}{file_ext}")
        with open(temp_input_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        processed_wav_path = temp_input_path
        is_wav = False
        try:
            with open(temp_input_path, "rb") as f:
                header = f.read(4)
            is_wav = header == b"RIFF"
        except Exception:
            pass

        if not is_wav or file_ext != ".wav":
            processed_wav_path = os.path.join(temp_dir, f"converted_{current_idx}.wav")
            convert_webm_to_wav(temp_input_path, processed_wav_path)

        waveform, meta = load_and_preprocess(processed_wav_path)
        rms_db, peak = compute_audio_quality(waveform)

        min_rms = config.enrollment.min_rms_db
        max_peak = config.enrollment.max_clip_peak

        sample_id = f"sample_{session_id}_{current_idx+1:04d}"
        target_dir = os.path.join("DATA")
        os.makedirs(target_dir, exist_ok=True)
        final_wav_path = os.path.join(target_dir, f"{sample_id}.wav")
        shutil.copyfile(processed_wav_path, final_wav_path)

        # Quality Gate Check
        if rms_db < min_rms or peak > max_peak:
            reason = f"Low volume (RMS {rms_db:.1f} dB < {min_rms} dB)" if rms_db < min_rms else f"Audio clipping detected (peak {peak:.2f} > {max_peak})"
            logger.warning(f"Clip quality rejected for sample {sample_id}: {reason}")
            
            append_to_manifest({
                "sample_id": sample_id,
                "session_id": session_id,
                "speaker_id": active_enrollment_session["speaker_id"],
                "device_name": active_enrollment_session["device_name"],
                "room_tag": active_enrollment_session["room_tag"],
                "file_path": final_wav_path,
                "phrase_index": current_idx + 1,
                "phrase_text": phrase_text,
                "is_holdout": is_holdout,
                "rms_db": round(rms_db, 2),
                "peak_amplitude": round(peak, 4),
                "status": "REJECTED_QUALITY",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

            await send_ws_quality_warning(session_id, reason, rms_db, peak, current_idx)
            return {
                "success": False,
                "quality_rejected": True,
                "reason": reason,
                "rms_db": rms_db,
                "peak": peak,
                "repeat_phrase": True,
                "current_phrase_index": current_idx,
                "phrase_text": phrase_text
            }

        # Valid quality clip
        append_to_manifest({
            "sample_id": sample_id,
            "session_id": session_id,
            "speaker_id": active_enrollment_session["speaker_id"],
            "device_name": active_enrollment_session["device_name"],
            "room_tag": active_enrollment_session["room_tag"],
            "file_path": final_wav_path,
            "phrase_index": current_idx + 1,
            "phrase_text": phrase_text,
            "is_holdout": is_holdout,
            "rms_db": round(rms_db, 2),
            "peak_amplitude": round(peak, 4),
            "status": "OK",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

        active_enrollment_session["valid_clips"] += 1
        active_enrollment_session["current_phrase_index"] += 1
        next_idx = active_enrollment_session["current_phrase_index"]
        total_target = len(phrases)

        await send_ws_progress(session_id, next_idx, total_target, f"Recorded clip {next_idx}/{total_target}")

        # Check if session completed all phrases
        if next_idx >= total_target:
            logger.info(f"All {total_target} clips recorded for session {session_id}. Running post-session enrollment...")
            result = enroll.run(session_id)
            active_enrollment_session["status"] = "FINALIZED"
            await send_ws_complete(session_id, result.get("success", False), result)
            return {
                "success": True,
                "session_completed": True,
                "clip_accepted": True,
                "enroll_result": result
            }

        return {
            "success": True,
            "clip_accepted": True,
            "next_phrase_index": next_idx,
            "next_phrase_text": phrases[next_idx] if next_idx < len(phrases) else None,
            "is_holdout": is_holdout
        }

    except Exception as e:
        logger.error(f"Error processing session clip: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/session/stop")
async def stop_session_endpoint(session_id: str = Form(...)):
    """Finalize an active session and execute backend/enroll.py"""
    global active_enrollment_session
    result = enroll.run(session_id)
    if active_enrollment_session and active_enrollment_session.get("session_id") == session_id:
        active_enrollment_session["status"] = "FINALIZED"
    await send_ws_complete(session_id, result.get("success", False), result)
    return {"success": True, "result": result}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", config.server.port))
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=port,
        reload=False
    )
