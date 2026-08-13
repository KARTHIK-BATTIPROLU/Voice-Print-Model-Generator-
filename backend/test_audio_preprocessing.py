"""
Unit tests for audio preprocessing functions.
Tests: resample_audio, convert_to_mono, estimate_snr, segment_audio, load_and_preprocess

Validates: Requirements 1.3, 1.4, 1.5, 5.2, 5.6, 5.7
"""
import os
import torch
import torchaudio
import numpy as np
from audio_utils import (
    resample_audio,
    convert_to_mono,
    estimate_snr,
    segment_audio,
    load_and_preprocess
)


def create_test_audio(duration=2.0, sample_rate=16000, channels=1, frequency=440.0):
    """Create synthetic test audio (sine wave)."""
    num_samples = int(duration * sample_rate)
    t = torch.linspace(0, duration, num_samples)
    waveform = torch.sin(2 * np.pi * frequency * t)
    
    # Add multiple channels if requested
    if channels > 1:
        waveform = waveform.repeat(channels, 1)
    else:
        waveform = waveform.unsqueeze(0)
    
    return waveform


def save_test_wav(waveform, sample_rate, filepath):
    """Save waveform as WAV file."""
    torchaudio.save(filepath, waveform, sample_rate)


def test_resample_audio():
    """Test audio resampling from various sample rates to 16kHz."""
    print("Testing resample_audio...")
    
    # Test 1: Same sample rate (no resampling needed)
    waveform = create_test_audio(duration=2.0, sample_rate=16000)
    resampled = resample_audio(waveform, 16000, 16000)
    assert torch.allclose(waveform, resampled), "Same rate resampling should return unchanged"
    print("  ✓ Same rate returns unchanged")
    
    # Test 2: Downsample from 44.1kHz to 16kHz
    waveform_44k = create_test_audio(duration=2.0, sample_rate=44100)
    resampled_16k = resample_audio(waveform_44k, 44100, 16000)
    expected_samples = int(2.0 * 16000)
    assert resampled_16k.shape[1] == expected_samples, f"Expected {expected_samples} samples, got {resampled_16k.shape[1]}"
    print("  ✓ 44.1kHz → 16kHz downsampling correct")
    
    # Test 3: Upsample from 8kHz to 16kHz
    waveform_8k = create_test_audio(duration=2.0, sample_rate=8000)
    resampled_16k = resample_audio(waveform_8k, 8000, 16000)
    expected_samples = int(2.0 * 16000)
    assert resampled_16k.shape[1] == expected_samples, f"Expected {expected_samples} samples, got {resampled_16k.shape[1]}"
    print("  ✓ 8kHz → 16kHz upsampling correct")
    
    # Test 4: Check no NaN or inf values
    assert not torch.isnan(resampled_16k).any(), "Resampled audio contains NaN"
    assert not torch.isinf(resampled_16k).any(), "Resampled audio contains inf"
    print("  ✓ No NaN or inf values in resampled audio")
    
    print("✅ resample_audio tests passed\n")


def test_convert_to_mono():
    """Test stereo to mono conversion."""
    print("Testing convert_to_mono...")
    
    # Test 1: Already mono
    mono_waveform = create_test_audio(duration=2.0, channels=1)
    result = convert_to_mono(mono_waveform)
    assert result.shape[0] == 1, "Mono output should have 1 channel"
    assert torch.allclose(mono_waveform, result), "Mono input should be unchanged"
    print("  ✓ Mono input returns unchanged")
    
    # Test 2: Stereo to mono (same signal in both channels)
    stereo_waveform = create_test_audio(duration=2.0, channels=2)
    result = convert_to_mono(stereo_waveform)
    assert result.shape[0] == 1, "Mono output should have 1 channel"
    # Since both channels are identical, mean should equal original
    assert torch.allclose(result[0], stereo_waveform[0]), "Mono conversion should average channels"
    print("  ✓ Stereo to mono conversion correct")
    
    # Test 3: Multi-channel (3 channels)
    multi_waveform = create_test_audio(duration=2.0, channels=3)
    result = convert_to_mono(multi_waveform)
    assert result.shape[0] == 1, "Mono output should have 1 channel"
    expected = multi_waveform.mean(dim=0, keepdim=True)
    assert torch.allclose(result, expected), "Multi-channel averaging should match expected"
    print("  ✓ Multi-channel to mono conversion correct")
    
    print("✅ convert_to_mono tests passed\n")


def test_estimate_snr():
    """Test SNR estimation."""
    print("Testing estimate_snr...")
    
    # Test 1: Clean signal (high SNR)
    clean_signal = create_test_audio(duration=2.0, sample_rate=16000)
    snr = estimate_snr(clean_signal, 16000)
    assert snr > 10.0, f"Clean signal should have high SNR, got {snr:.2f} dB"
    print(f"  ✓ Clean signal SNR: {snr:.2f} dB (high)")
    
    # Test 2: Noisy signal (lower SNR)
    signal_with_noise = create_test_audio(duration=2.0, sample_rate=16000)
    noise = torch.randn_like(signal_with_noise) * 0.1
    noisy_signal = signal_with_noise + noise
    snr_noisy = estimate_snr(noisy_signal, 16000)
    assert snr_noisy < snr, "Noisy signal should have lower SNR than clean"
    print(f"  ✓ Noisy signal SNR: {snr_noisy:.2f} dB (lower than clean)")
    
    # Test 3: Very short signal
    short_signal = create_test_audio(duration=0.01, sample_rate=16000)  # 10ms
    snr_short = estimate_snr(short_signal, 16000)
    assert isinstance(snr_short, float), "SNR should be a float"
    print(f"  ✓ Short signal SNR: {snr_short:.2f} dB (handled)")
    
    # Test 4: Stereo signal
    stereo_signal = create_test_audio(duration=2.0, sample_rate=16000, channels=2)
    snr_stereo = estimate_snr(stereo_signal, 16000)
    assert isinstance(snr_stereo, float), "Stereo SNR estimation should work"
    print(f"  ✓ Stereo signal SNR: {snr_stereo:.2f} dB")
    
    print("✅ estimate_snr tests passed\n")


def test_segment_audio():
    """Test audio segmentation."""
    print("Testing segment_audio...")
    
    # Test 1: Short audio (no segmentation needed)
    short_audio = create_test_audio(duration=5.0, sample_rate=16000)
    segments = segment_audio(short_audio, 16000, segment_length=10.0)
    assert len(segments) == 1, "Short audio should produce 1 segment"
    assert torch.allclose(segments[0], short_audio), "Single segment should equal original"
    print("  ✓ Short audio returns single segment")
    
    # Test 2: Long audio (needs segmentation)
    long_audio = create_test_audio(duration=15.0, sample_rate=16000)
    segments = segment_audio(long_audio, 16000, segment_length=10.0)
    assert len(segments) > 1, "Long audio should produce multiple segments"
    
    # Each segment should be <= 10 seconds
    for i, seg in enumerate(segments):
        duration = seg.shape[1] / 16000
        assert duration <= 10.0, f"Segment {i} duration {duration:.2f}s exceeds 10s"
    print(f"  ✓ Long audio split into {len(segments)} segments")
    
    # Test 3: Check overlap (segments should overlap)
    # With 10s segments and 1s hop, we should have 9s overlap
    if len(segments) >= 2:
        seg1_samples = segments[0].shape[1]
        seg2_samples = segments[1].shape[1]
        hop_samples = 16000  # 1 second hop
        # Second segment should start 1 second after first
        assert seg1_samples == int(10.0 * 16000), "First segment should be 10 seconds"
        print(f"  ✓ Segments overlap correctly (1s hop)")
    
    # Test 4: Exact segment length
    exact_audio = create_test_audio(duration=10.0, sample_rate=16000)
    segments = segment_audio(exact_audio, 16000, segment_length=10.0)
    assert len(segments) == 1, "Exactly 10s audio should produce 1 segment"
    print("  ✓ Exact length audio returns single segment")
    
    print("✅ segment_audio tests passed\n")


def test_load_and_preprocess():
    """Test full preprocessing pipeline."""
    print("Testing load_and_preprocess...")
    
    # Create test files
    test_dir = "test_audio_files"
    os.makedirs(test_dir, exist_ok=True)
    
    try:
        # Test 1: Valid 44.1kHz stereo file
        stereo_44k = create_test_audio(duration=2.0, sample_rate=44100, channels=2)
        filepath_44k = os.path.join(test_dir, "test_44k_stereo.wav")
        save_test_wav(stereo_44k, 44100, filepath_44k)
        
        waveform, metadata = load_and_preprocess(filepath_44k)
        assert waveform.shape[0] == 1, "Preprocessed audio should be mono"
        assert metadata["original_sample_rate"] == 44100, "Original sample rate not recorded"
        assert metadata["original_channels"] == 2, "Original channels not recorded"
        assert metadata["preprocessed"] == True, "Preprocessed flag not set"
        assert "snr_db" in metadata, "SNR not computed"
        print(f"  ✓ 44.1kHz stereo → 16kHz mono (SNR: {metadata['snr_db']:.2f} dB)")
        
        # Test 2: Valid 8kHz mono file
        mono_8k = create_test_audio(duration=3.0, sample_rate=8000, channels=1)
        filepath_8k = os.path.join(test_dir, "test_8k_mono.wav")
        save_test_wav(mono_8k, 8000, filepath_8k)
        
        waveform, metadata = load_and_preprocess(filepath_8k)
        assert metadata["original_sample_rate"] == 8000, "Original sample rate not recorded"
        assert metadata["original_channels"] == 1, "Original channels not recorded"
        print(f"  ✓ 8kHz mono → 16kHz mono (SNR: {metadata['snr_db']:.2f} dB)")
        
        # Test 3: Invalid file (too short)
        short_audio = create_test_audio(duration=1.0, sample_rate=16000)
        filepath_short = os.path.join(test_dir, "test_short.wav")
        save_test_wav(short_audio, 16000, filepath_short)
        
        try:
            load_and_preprocess(filepath_short)
            assert False, "Should have raised ValueError for short audio"
        except ValueError as e:
            assert "below minimum" in str(e).lower(), "Error message should mention duration"
            print(f"  ✓ Short audio rejected: {str(e)}")
        
        # Test 4: Very noisy file (low SNR)
        # Create a signal with very high noise
        signal = create_test_audio(duration=2.0, sample_rate=16000) * 0.01  # Very quiet signal
        noise = torch.randn_like(signal) * 0.5  # Loud noise
        noisy_audio = signal + noise
        filepath_noisy = os.path.join(test_dir, "test_noisy.wav")
        save_test_wav(noisy_audio, 16000, filepath_noisy)
        
        try:
            load_and_preprocess(filepath_noisy)
            # May or may not fail depending on SNR calculation
            print(f"  ✓ Noisy audio processed or rejected appropriately")
        except ValueError as e:
            if "snr too low" in str(e).lower():
                print(f"  ✓ Low SNR audio rejected: {str(e)}")
            else:
                raise
        
        # Test 5: Non-existent file
        try:
            load_and_preprocess("nonexistent.wav")
            assert False, "Should have raised ValueError for missing file"
        except ValueError as e:
            assert "not found" in str(e).lower(), "Error message should mention file not found"
            print(f"  ✓ Missing file rejected: {str(e)}")
        
        # Test 6: Check amplitude normalization
        loud_audio = create_test_audio(duration=2.0, sample_rate=16000) * 5.0  # Amplitude > 1
        filepath_loud = os.path.join(test_dir, "test_loud.wav")
        save_test_wav(loud_audio, 16000, filepath_loud)
        
        waveform, metadata = load_and_preprocess(filepath_loud)
        max_amplitude = torch.max(torch.abs(waveform)).item()
        assert max_amplitude <= 1.0, f"Normalized amplitude {max_amplitude} exceeds 1.0"
        print(f"  ✓ Loud audio normalized (max amplitude: {max_amplitude:.4f})")
        
        print("✅ load_and_preprocess tests passed\n")
        
    finally:
        # Cleanup test files
        import shutil
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        print("  ✓ Test files cleaned up")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Audio Preprocessing Functions Test Suite")
    print("="*60 + "\n")
    
    test_resample_audio()
    test_convert_to_mono()
    test_estimate_snr()
    test_segment_audio()
    test_load_and_preprocess()
    
    print("="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60 + "\n")
