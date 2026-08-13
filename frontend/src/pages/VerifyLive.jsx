import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getProfiles, verifyLive } from '../api/api';
import { WaveformRing, ScoreGauge } from '../components';
import './VerifyLive.css';

export default function VerifyLive() {
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState('');
  const [recording, setRecording] = useState(false);
  const [audioStream, setAudioStream] = useState(null);
  const [duration, setDuration] = useState(0);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const navigate = useNavigate();
  const location = useLocation();

  // Load profiles and parse query param
  useEffect(() => {
    const fetchProfiles = async () => {
      try {
        const data = await getProfiles();
        setProfiles(data);
        
        // Select profile from query params if available
        const params = new URLSearchParams(location.search);
        const profileParam = params.get('profile');
        if (profileParam && data.some((p) => p.name === profileParam)) {
          setSelectedProfile(profileParam);
        } else if (data.length > 0) {
          setSelectedProfile(data[0].name);
        }
      } catch (err) {
        setError('Failed to fetch speaker profiles: ' + err.message);
      }
    };
    fetchProfiles();
  }, [location]);

  // Duration timer
  useEffect(() => {
    let timer;
    if (recording) {
      timer = setInterval(() => {
        setDuration((prev) => prev + 0.1);
      }, 100);
    }
    return () => clearInterval(timer);
  }, [recording]);

  const startRecording = async () => {
    if (!selectedProfile) {
      setError('Please select a profile first');
      return;
    }

    chunksRef.current = [];
    setError(null);
    setResult(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setAudioStream(stream);

      let options = { mimeType: 'audio/webm' };
      let recorder;
      try {
        recorder = new MediaRecorder(stream, options);
      } catch (e) {
        // Fallback for browsers that don't support audio/webm
        recorder = new MediaRecorder(stream);
      }

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop());
        handleVerify(blob);
      };

      mediaRecorderRef.current = recorder;
      recorder.start(250); // Get chunks every 250ms
      setRecording(true);
      setDuration(0);
    } catch (err) {
      setError('Microphone access denied or error initializing: ' + err.message);
    }
  };

  const stopRecording = () => {
    if (duration < 1.5) {
      setError('Recording is too short. Please speak for at least 1.5 seconds.');
      if (mediaRecorderRef.current && recording) {
        mediaRecorderRef.current.stop();
        setRecording(false);
        setAudioStream(null);
      }
      return;
    }

    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
      setAudioStream(null);
    }
  };

  const handleVerify = async (blob) => {
    setAnalyzing(true);
    setError(null);
    try {
      const data = await verifyLive(selectedProfile, blob);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Verification failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const getProfileThreshold = () => {
    const profile = profiles.find((p) => p.name === selectedProfile);
    return profile ? (profile.metadata.threshold || 0.7) : 0.7;
  };

  return (
    <div className="verify-live-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Live Voice Verification</h1>
          <p className="page-subtitle">Verify speaker identity using real-time microphone capture.</p>
        </div>
        <button className="btn-secondary" onClick={() => navigate('/')}>
          Back to Dashboard
        </button>
      </div>

      <div className="verify-live-container">
        <div className="verify-setup-panel">
          <div className="form-group">
            <label htmlFor="profileSelect" className="form-label">
              Select Profile to Verify Against
            </label>
            <select
              id="profileSelect"
              className="form-select"
              value={selectedProfile}
              onChange={(e) => {
                setSelectedProfile(e.target.value);
                setResult(null);
                setError(null);
              }}
              disabled={recording || analyzing}
            >
              {profiles.length === 0 ? (
                <option value="">No profiles available</option>
              ) : (
                profiles.map((p) => (
                  <option key={p.name} value={p.name}>
                    {p.name} (threshold: {(p.metadata.threshold || 0.7).toFixed(2)})
                  </option>
                ))
              )}
            </select>
          </div>
        </div>

        <div className="verify-workspace">
          <div className="visualization-section">
            <WaveformRing
              audioStream={audioStream}
              size={240}
              isRecording={recording}
            />

            {recording && (
              <div className="timer-badge">
                <span className="live-dot"></span>
                <span>Recording: {duration.toFixed(1)}s</span>
              </div>
            )}

            <div className="control-buttons">
              {!recording ? (
                <button
                  className="btn-verify-action start"
                  onClick={startRecording}
                  disabled={analyzing || !selectedProfile}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" strokeWidth="2"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" strokeWidth="2"/>
                    <line x1="12" y1="19" x2="12" y2="23" strokeWidth="2"/>
                  </svg>
                  Start Recording
                </button>
              ) : (
                <button
                  className="btn-verify-action stop"
                  onClick={stopRecording}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <rect x="4" y="4" width="16" height="16" rx="2" strokeWidth="2"/>
                  </svg>
                  Stop & Verify
                </button>
              )}
            </div>

            {analyzing && (
              <div className="analyzing-indicator">
                <div className="pulse-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <p>Analyzing voiceprint matching...</p>
              </div>
            )}
          </div>

          <div className="results-section">
            {error && (
              <div className="error-box">
                <svg className="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <circle cx="12" cy="12" r="10" strokeWidth="2"/>
                  <line x1="12" y1="8" x2="12" y2="12" strokeWidth="2"/>
                  <line x1="12" y1="16" x2="12.01" y2="16" strokeWidth="2"/>
                </svg>
                <p>{error}</p>
              </div>
            )}

            {result && result.success && (
              <div className={`verification-result-card ${result.verified ? 'passed' : 'failed'}`}>
                <div className="result-header">
                  <div className={`status-badge ${result.verified ? 'verified' : 'denied'}`}>
                    {result.verified ? (
                      <>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="badge-icon">
                          <polyline points="20 6 9 17 4 12" strokeWidth="3" strokeLinecap="round"/>
                        </svg>
                        <span>Access Granted</span>
                      </>
                    ) : (
                      <>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="badge-icon">
                          <line x1="18" y1="6" x2="6" y2="18" strokeWidth="3" strokeLinecap="round"/>
                          <line x1="6" y1="6" x2="18" y2="18" strokeWidth="3" strokeLinecap="round"/>
                        </svg>
                        <span>Access Denied</span>
                      </>
                    )}
                  </div>
                </div>

                <div className="gauge-container">
                  <ScoreGauge
                    score={result.similarityScore}
                    threshold={result.threshold}
                    size={220}
                  />
                </div>

                <div className="result-details">
                  <div className="detail-row">
                    <span>Speaker Name</span>
                    <strong>{result.profileName}</strong>
                  </div>
                  <div className="detail-row">
                    <span>Similarity Score</span>
                    <strong className="score-value">{result.similarityScore.toFixed(4)}</strong>
                  </div>
                  <div className="detail-row">
                    <span>Required Threshold</span>
                    <strong>{result.threshold.toFixed(2)}</strong>
                  </div>
                  <div className="detail-row">
                    <span>Match Status</span>
                    <strong className={result.verified ? 'status-text success' : 'status-text error'}>
                      {result.verified ? 'MATCH SUCCESS' : 'MATCH FAILED'}
                    </strong>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
