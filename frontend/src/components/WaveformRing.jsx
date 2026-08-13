import { useEffect, useRef, useState } from 'react';
import './WaveformRing.css';

/**
 * WaveformRing Component
 * 
 * Real-time circular waveform visualization using Web Audio API.
 * Uses AnalyserNode to get frequency data and renders it as a circular waveform.
 * 
 * @param {Object} props
 * @param {MediaStream} props.audioStream - Audio stream from microphone
 * @param {number} [props.size=200] - Canvas size in pixels
 * @param {boolean} [props.isRecording=false] - Whether recording is active
 */
export default function WaveformRing({
  audioStream,
  size = 200,
  isRecording = false
}) {
  const canvasRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize Web Audio API
  useEffect(() => {
    if (!audioStream || !isRecording) {
      return;
    }

    // Create audio context and analyser
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256; // Power of 2, smaller = less detail but faster
    analyser.smoothingTimeConstant = 0.8; // Smooth out rapid changes

    // Connect audio stream to analyser
    const source = audioContext.createMediaStreamSource(audioStream);
    source.connect(analyser);

    audioContextRef.current = audioContext;
    analyserRef.current = analyser;
    setIsInitialized(true);

    // Cleanup function
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (source) {
        source.disconnect();
      }
      if (audioContext) {
        audioContext.close();
      }
      setIsInitialized(false);
    };
  }, [audioStream, isRecording]);

  // Animation loop
  useEffect(() => {
    if (!isInitialized || !analyserRef.current || !canvasRef.current) {
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    // Center coordinates
    const centerX = size / 2;
    const centerY = size / 2;
    const baseRadius = size * 0.25;
    const maxAmplitude = size * 0.15;

    const draw = () => {
      // Get frequency data
      analyser.getByteFrequencyData(dataArray);

      // Clear canvas
      ctx.clearRect(0, 0, size, size);

      // Calculate average volume for color gradient
      const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;
      const normalizedVolume = average / 255;

      // Draw circular waveform
      ctx.beginPath();
      ctx.strokeStyle = getWaveformColor(normalizedVolume);
      ctx.lineWidth = 3;

      const sliceAngle = (Math.PI * 2) / bufferLength;

      for (let i = 0; i < bufferLength; i++) {
        const angle = sliceAngle * i - Math.PI / 2;
        const amplitude = (dataArray[i] / 255) * maxAmplitude;
        const radius = baseRadius + amplitude;

        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }

      ctx.closePath();
      ctx.stroke();

      // Draw inner circle for visual anchor
      ctx.beginPath();
      ctx.arc(centerX, centerY, baseRadius * 0.3, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(108, 99, 255, 0.2)';
      ctx.fill();

      // Draw center recording indicator
      if (isRecording) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, baseRadius * 0.15, 0, Math.PI * 2);
        ctx.fillStyle = getWaveformColor(normalizedVolume);
        ctx.fill();

        // Pulsing effect
        const pulseRadius = baseRadius * 0.15 + (normalizedVolume * 5);
        ctx.beginPath();
        ctx.arc(centerX, centerY, pulseRadius, 0, Math.PI * 2);
        ctx.strokeStyle = getWaveformColor(normalizedVolume);
        ctx.lineWidth = 2;
        ctx.globalAlpha = 0.5 * (1 - normalizedVolume);
        ctx.stroke();
        ctx.globalAlpha = 1;
      }

      // Continue animation at ~30fps
      animationFrameRef.current = requestAnimationFrame(draw);
    };

    // Start animation
    draw();

    // Cleanup
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isInitialized, isRecording, size]);

  // Helper function to determine waveform color based on volume
  function getWaveformColor(volume) {
    if (volume < 0.2) {
      return 'var(--accent)'; // Low volume - accent color
    } else if (volume < 0.5) {
      return 'var(--success)'; // Medium volume - green
    } else if (volume < 0.8) {
      return 'var(--warning)'; // High volume - yellow
    } else {
      return 'var(--error)'; // Very high volume - red (clipping warning)
    }
  }

  return (
    <div className="waveform-ring-container">
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        className="waveform-ring-canvas"
        style={{ width: size, height: size }}
      />
      {!isRecording && (
        <div className="waveform-ring-placeholder">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <line x1="12" y1="19" x2="12" y2="23" strokeWidth="2" strokeLinecap="round"/>
            <line x1="8" y1="23" x2="16" y2="23" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          <p>Start recording to see waveform</p>
        </div>
      )}
    </div>
  );
}
