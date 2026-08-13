"""
Unit tests for audio validation function.
Tests validate_wav against requirements 1.2, 5.1, 5.3, 5.4
"""
import os
import tempfile
import numpy as np
import torchaudio
from audio_utils import validate_wav


def create_test_wav(file_path: str, sample_rate: int, duration: float, channels: int = 1):
    """Helper function to create test WAV files"""
    num_samples = int(sample_rate * duration)
    # Generate simple sine wave
    frequency = 440  # A4 note
    t = np.linspace(0, duration, num_samples)
    waveform = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    # Create multi-channel if requested
    if channels > 1:
        waveform = np.stack([waveform] * channels)
    else:
        waveform = waveform.reshape(1, -1)
    
    # Save as WAV
    import torch
    torchaudio.save(file_path, torch.from_numpy(waveform), sample_rate)


def test_valid_wav():
    """Test validation of a valid WAV file"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
    
    try:
        # Create valid WAV: 16kHz, 2 seconds, mono
        create_test_wav(temp_path, 16000, 2.0, 1)
        
        result = validate_wav(temp_path)
        
        assert result["valid"] == True, "Valid WAV should pass validation"
        assert result["sample_rate"] == 16000, "Sample rate should be 16000"
        assert result["channels"] == 1, "Should have 1 channel"
        assert result["duration"] >= 1.5, "Duration should be at least 1.5 seconds"
        assert result["error"] is None, "No error should be present"
        
        print("✓ test_valid_wav passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_file_not_found():
    """Test validation when file doesn't exist"""
    result = validate_wav("nonexistent_file.wav")
    
    assert result["valid"] == False, "Non-existent file should fail validation"
    assert result["error"] == "File not found", "Should return 'File not found' error"
    
    print("✓ test_file_not_found passed")


def test_sample_rate_too_low():
    """Test rejection of sample rate below 8kHz"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
    
    try:
        # Create WAV with 7kHz sample rate (below minimum)
        create_test_wav(temp_path, 7000, 2.0, 1)
        
        result = validate_wav(temp_path)
        
        assert result["valid"] == False, "Sample rate below 8kHz should fail"
        assert "Sample rate 7000 Hz outside valid range" in result["error"], \
            "Should indicate sample rate out of range"
        
        print("✓ test_sample_rate_too_low passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_sample_rate_too_high():
    """Test rejection of sample rate above 48kHz"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
    
    try:
        # Create WAV with 50kHz sample rate (above maximum)
        create_test_wav(temp_path, 50000, 2.0, 1)
        
        result = validate_wav(temp_path)
        
        assert result["valid"] == False, "Sample rate above 48kHz should fail"
        assert "Sample rate 50000 Hz outside valid range" in result["error"], \
            "Should indicate sample rate out of range"
        
        print("✓ test_sample_rate_too_high passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_sample_rate_boundary_8khz():
    """Test acceptance of 8kHz sample rate (lower boundary)"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
    
    try:
        create_test_wav(temp_path, 8000, 2.0, 1)
        
        result = validate_wav(temp_path)
        
        assert result["valid"] == True, "8kHz should be accepted (boundary)"
        assert result["sample_rate"] == 8000, "Sample rate should be 8000"
        
        print("✓ test_sample_rate_boundary_8khz passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_sample_rate_boundary_48khz():
    """Test acceptance of 48kHz sample rate (upper boundary)"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
    
    try:
        create_test_wav(temp_path, 48000, 2.0, 1)
        
        result = validate_wav(temp_path)
        
        assert result["valid"] == True, "48kHz should be accepted (boundary)"
        assert result["sample_rate"] == 48000, "Sample rate should be 48000"
        
        print("✓ test_sample_rate_boundary_48khz passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_duration_too_short():
    """Test rejection of audio shorter than 1.5 seconds"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
    
    try:
        # Create WAV with 1.0 second duration (below minimum)
        create_test_wav(temp_path, 16000, 1.0, 1)
        
        result = validate_wav(temp_path)
        
        assert result["valid"] == False, "Duration below 1.5s should fail"
        assert "Audio duration" in result["error"] and "below minimum 1.5 seconds" in result["error"], \
            "Should indicate duration too short"
        
        print("✓ test_duration_too_short passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_duration_boundary():
    """Test acceptance of audio at exactly 1.5 seconds"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
    
    try:
        # Create WAV with exactly 1.5 seconds
        create_test_wav(temp_path, 16000, 1.5, 1)
        
        result = validate_wav(temp_path)
        
        assert result["valid"] == True, "1.5s duration should be accepted (boundary)"
        assert result["duration"] >= 1.5, "Duration should be at least 1.5 seconds"
        
        print("✓ test_duration_boundary passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_stereo_audio():
    """Test validation of stereo audio"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
    
    try:
        # Create stereo WAV
        create_test_wav(temp_path, 16000, 2.0, 2)
        
        result = validate_wav(temp_path)
        
        assert result["valid"] == True, "Valid stereo audio should pass"
        assert result["channels"] == 2, "Should detect 2 channels"
        
        print("✓ test_stereo_audio passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_corrupted_file():
    """Test rejection of corrupted/invalid WAV file"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Write garbage data
        f.write(b"Not a valid WAV file")
        temp_path = f.name
    
    try:
        result = validate_wav(temp_path)
        
        assert result["valid"] == False, "Corrupted file should fail validation"
        assert result["error"] == "Invalid WAV format or corrupted file", \
            "Should return 'Invalid WAV format or corrupted file' error"
        
        print("✓ test_corrupted_file passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_metadata_returned():
    """Test that all metadata fields are returned correctly"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
    
    try:
        create_test_wav(temp_path, 22050, 3.0, 1)
        
        result = validate_wav(temp_path)
        
        # Check all required fields are present
        assert "valid" in result, "Result should contain 'valid' field"
        assert "sample_rate" in result, "Result should contain 'sample_rate' field"
        assert "channels" in result, "Result should contain 'channels' field"
        assert "duration" in result, "Result should contain 'duration' field"
        assert "error" in result, "Result should contain 'error' field"
        
        # Check values are correct
        assert result["sample_rate"] == 22050, "Sample rate should be 22050"
        assert result["channels"] == 1, "Channels should be 1"
        assert 2.9 < result["duration"] < 3.1, "Duration should be approximately 3.0s"
        
        print("✓ test_metadata_returned passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == "__main__":
    print("Running audio validation tests...")
    print()
    
    test_valid_wav()
    test_file_not_found()
    test_sample_rate_too_low()
    test_sample_rate_too_high()
    test_sample_rate_boundary_8khz()
    test_sample_rate_boundary_48khz()
    test_duration_too_short()
    test_duration_boundary()
    test_stereo_audio()
    test_corrupted_file()
    test_metadata_returned()
    
    print()
    print("All tests passed! ✓")
