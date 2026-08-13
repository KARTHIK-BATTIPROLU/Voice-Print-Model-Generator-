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
import logging
from typing import Optional, List, Dict
from datetime import datetime

import numpy as np
import torch
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False
    )
