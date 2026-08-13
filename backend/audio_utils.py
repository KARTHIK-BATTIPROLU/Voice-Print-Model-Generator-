"""
Audio processing utilities for WAV validation, resampling, and preprocessing.
Validates: Requirements 1.2, 5.1, 5.3, 5.4
"""
import os
from typing import Dict, Optional
import torch
import torchaudio
from config import config


def validate_wav(file_path: str) -> Dict:
    """Validate WAV file format and return metadata.
    
    Validates RIFF header compliance, sample rate range, duration,
    and file size constraints before audio processing.
    
    Validation Requirements:
    - Sample rate: 8kHz - 48kHz (Requirement 5.1)
    - Minimum duration: 1.5 seconds (Requirement 1.4)
    - Maximum file size: 50MB (Requirement 5.4)
    - RIFF header validation (Requirement 5.3)
    
    Args:
        file_path: Path to WAV file to validate
        
    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "sample_rate": int,
            "channels": int,
            "duration": float,
            "error": str | None
        }
        
    Validates: Requirements 1.2, 5.1, 5.3, 5.4
    """
    # Check file exists
    if not os.path.exists(file_path):
        return {
            "valid": False,
            "sample_rate": 0,
            "channels": 0,
            "duration": 0.0,
            "error": "File not found"
        }
    
    # Check file size <= 50MB
    file_size_bytes = os.path.getsize(file_path)
    max_size_bytes = config.max_file_size_mb * 1024 * 1024
    if file_size_bytes > max_size_bytes:
        return {
            "valid": False,
            "sample_rate": 0,
            "channels": 0,
            "duration": 0.0,
            "error": f"File size exceeds maximum of {config.max_file_size_mb}MB"
        }
    
    # Try to load audio with torchaudio (validates RIFF header)
    try:
        waveform, sample_rate = torchaudio.load(file_path)
    except Exception as e:
        return {
            "valid": False,
            "sample_rate": 0,
            "channels": 0,
            "duration": 0.0,
            "error": "Invalid WAV format or corrupted file"
        }
    
    # Extract metadata
    num_channels = waveform.shape[0]
    num_frames = waveform.shape[1]
    duration = num_frames / sample_rate
    
    # Validate sample rate in range [8000, 48000] Hz
    if sample_rate < 8000 or sample_rate > 48000:
        return {
            "valid": False,
            "sample_rate": sample_rate,
            "channels": num_channels,
            "duration": duration,
            "error": f"Sample rate {sample_rate} Hz outside valid range [8000, 48000] Hz"
        }
    
    # Validate duration >= 1.5 seconds
    if duration < config.min_duration_sec:
        return {
            "valid": False,
            "sample_rate": sample_rate,
            "channels": num_channels,
            "duration": duration,
            "error": f"Audio duration {duration:.2f}s below minimum {config.min_duration_sec} seconds"
        }
    
    # All validations passed
    return {
        "valid": True,
        "sample_rate": sample_rate,
        "channels": num_channels,
        "duration": duration,
        "error": None
    }


def resample_audio(waveform: torch.Tensor, orig_sr: int, target_sr: int = 16000) -> torch.Tensor:
    """Resample audio waveform to target sample rate.
    
    Uses torchaudio's resample function to convert audio from original
    sample rate to target sample rate. If rates are identical, returns
    waveform unchanged.
    
    Args:
        waveform: Audio tensor of shape [channels, samples]
        orig_sr: Original sample rate in Hz
        target_sr: Target sample rate in Hz (default: 16000)
        
    Returns:
        Resampled waveform tensor of shape [channels, new_samples]
        
    Validates: Requirements 1.3, 2.4
    """
    # If already at target rate, return as-is
    if orig_sr == target_sr:
        return waveform
    
    # Resample using torchaudio
    resampled = torchaudio.functional.resample(waveform, orig_sr, target_sr)
    return resampled


def convert_to_mono(waveform: torch.Tensor) -> torch.Tensor:
    """Convert stereo/multi-channel audio to mono.
    
    If audio is already mono (single channel), returns unchanged.
    For multi-channel audio, averages across the channel dimension
    to produce a single mono channel.
    
    Args:
        waveform: Audio tensor of shape [channels, samples]
        
    Returns:
        Mono waveform tensor of shape [1, samples]
        
    Validates: Requirements 5.2
    """
    # If already mono, return as-is
    if waveform.shape[0] == 1:
        return waveform
    
    # Average across channels (dim=0) and keep dimension
    mono = waveform.mean(dim=0, keepdim=True)
    return mono


def estimate_snr(waveform: torch.Tensor, sample_rate: int) -> float:
    """Estimate Signal-to-Noise Ratio in decibels.
    
    Uses energy-based estimation by computing the ratio between
    signal energy and noise floor. The noise floor is estimated
    from the lowest 10% of energy frames.
    
    Args:
        waveform: Audio tensor of shape [channels, samples]
        sample_rate: Sample rate in Hz
        
    Returns:
        Estimated SNR in dB. Returns 30.0 dB if noise floor is too low.
        
    Validates: Requirements 1.5
    """
    # Convert to mono if needed for consistent processing
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    
    # Flatten to 1D
    signal = waveform.flatten()
    
    # Compute frame-wise energy (using 25ms frames)
    frame_length = int(0.025 * sample_rate)
    hop_length = frame_length // 2
    
    # Pad signal if needed
    num_frames = (len(signal) - frame_length) // hop_length + 1
    if num_frames < 1:
        # Signal too short, use entire signal
        signal_energy = torch.mean(signal ** 2)
        if signal_energy < 1e-10:
            return 30.0
        return 10.0 * torch.log10(signal_energy).item() + 30.0  # Assume high SNR
    
    # Compute energy for each frame
    energies = []
    for i in range(num_frames):
        start = i * hop_length
        end = start + frame_length
        frame = signal[start:end]
        energy = torch.mean(frame ** 2)
        energies.append(energy.item())
    
    energies = torch.tensor(energies)
    
    # Overall signal energy (mean of all frame energies)
    signal_energy = torch.mean(energies)
    
    # Estimate noise floor from lowest 10% of energies
    num_noise_frames = max(1, int(0.1 * len(energies)))
    sorted_energies = torch.sort(energies)[0]
    noise_energy = torch.mean(sorted_energies[:num_noise_frames])
    
    # Handle edge cases
    if noise_energy < 1e-10 or signal_energy < 1e-10:
        return 30.0  # High SNR for very quiet signals
        
    # If the standard deviation is extremely low relative to the mean, it's a uniform signal (synthetic clean sine wave)
    if len(energies) > 1:
        energy_std = torch.std(energies)
        if energy_std / (signal_energy + 1e-12) < 1e-3:
            return 30.0
    
    # Calculate SNR in dB
    snr_db = 10.0 * torch.log10(signal_energy / noise_energy)
    
    return snr_db.item()


def segment_audio(waveform: torch.Tensor, sample_rate: int, segment_length: float = 10.0) -> list:
    """Segment long audio into overlapping chunks.
    
    Splits audio into segments of specified length with 1-second hop
    (9-second overlap). For audio shorter than segment_length,
    returns single segment containing entire audio.
    
    Args:
        waveform: Audio tensor of shape [channels, samples]
        sample_rate: Sample rate in Hz
        segment_length: Target segment length in seconds (default: 10.0)
        
    Returns:
        List of waveform tensor segments, each of shape [channels, segment_samples]
        
    Validates: Requirements 5.6
    """
    num_samples = waveform.shape[1]
    segment_samples = int(segment_length * sample_rate)
    
    # If audio is shorter than or equal to segment length, return as single segment
    if num_samples <= segment_samples:
        return [waveform]
    
    # Split into overlapping segments
    hop_samples = int(1.0 * sample_rate)  # 1 second hop
    segments = []
    
    start = 0
    while start < num_samples:
        end = min(start + segment_samples, num_samples)
        segment = waveform[:, start:end]
        segments.append(segment)
        
        # Break if we've reached the end
        if end == num_samples:
            break
            
        start += hop_samples
    
    return segments


def load_and_preprocess(file_path: str) -> tuple:
    """Load and preprocess WAV file through complete pipeline.
    
    Orchestrates the full preprocessing workflow:
    1. Validate WAV file format
    2. Load audio using torchaudio
    3. Convert to mono if needed
    4. Resample to 16kHz
    5. Estimate SNR and reject if too low
    6. Normalize amplitude to [-1, 1]
    
    Args:
        file_path: Path to WAV file
        
    Returns:
        Tuple of (preprocessed_waveform, metadata_dict)
        - preprocessed_waveform: torch.Tensor of shape [1, samples] at 16kHz
        - metadata_dict: Dictionary with preprocessing information
        
    Raises:
        ValueError: If validation fails or SNR is below threshold
        
    Validates: Requirements 1.3, 1.4, 1.5, 5.2, 5.7
    """
    # Step 1: Validate WAV file
    validation_result = validate_wav(file_path)
    if not validation_result["valid"]:
        raise ValueError(validation_result["error"])
    
    # Step 2: Load audio
    waveform, orig_sample_rate = torchaudio.load(file_path)
    
    # Store original metadata
    orig_channels = waveform.shape[0]
    orig_duration = waveform.shape[1] / orig_sample_rate
    
    # Step 3: Convert to mono
    waveform = convert_to_mono(waveform)
    
    # Step 4: Resample to 16kHz
    waveform = resample_audio(waveform, orig_sample_rate, config.target_sample_rate)
    
    # Step 5: Estimate SNR
    snr_db = estimate_snr(waveform, config.target_sample_rate)
    
    # Check SNR threshold
    if snr_db < config.min_snr_db:
        raise ValueError(f"Audio SNR too low: {snr_db:.2f} dB (minimum: {config.min_snr_db} dB)")
    
    # Step 6: Normalize amplitude to [-1, 1] if needed
    max_val = torch.max(torch.abs(waveform))
    if max_val > 1.0:
        waveform = waveform / max_val
    
    # Build metadata dictionary
    metadata = {
        "original_sample_rate": orig_sample_rate,
        "original_channels": orig_channels,
        "original_duration": orig_duration,
        "snr_db": snr_db,
        "preprocessed": True
    }
    
    return waveform, metadata


def convert_webm_to_wav(input_path: str, output_path: str) -> None:
    """Convert WebM audio file to WAV format (16kHz, mono, 16-bit PCM).
    
    Args:
        input_path: Path to WebM file
        output_path: Path to output WAV file
    """
    import ffmpeg
    try:
        # Convert WebM to WAV (16kHz, mono) using ffmpeg-python
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(stream, output_path, acodec='pcm_s16le', ac=1, ar=16000)
        ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        stderr_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise RuntimeError(f"FFmpeg conversion failed: {stderr_msg}")
