import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { startSession, sendSessionClip, stopSession, resetSession, getSessionStatus, connectProgressWebSocket } from '../api/api';
import { ProgressRing } from '../components';
import './Enroll.css';

const SCRIPTED_PHRASES = [
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
];

export default function Enroll() {
  const [roomTag, setRoomTag] = useState('bedroom-laptop-mic');
  const [speakerId, setSpeakerId] = useState('ASTA_primary');
  const [activeSession, setActiveSession] = useState(null);
  const [currentPhraseIdx, setCurrentPhraseIdx] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMsg, setProgressMsg] = useState('');
  const [qualityWarning, setQualityWarning] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if session is already active
    getSessionStatus()
      .then(res => {
        if (res.active && res.session) {
          setActiveSession(res.session);
          setCurrentPhraseIdx(res.session.current_phrase_index || 0);
        }
      })
      .catch(console.error);
  }, []);

  const handleStartSession = async (e) => {
    e.preventDefault();
    setError(null);
    setQualityWarning(null);
    try {
      const res = await startSession(roomTag, speakerId);
      if (res.success && res.session) {
        setActiveSession(res.session);
        setCurrentPhraseIdx(0);
      }
    } catch (err) {
      if (err.status === 409) {
        setError('An active session already exists. Click "Reset Session" below if you wish to start fresh.');
      } else {
        setError(err.message || 'Failed to start session');
      }
    }
  };

  const handleResetSession = async () => {
    try {
      await resetSession();
      setActiveSession(null);
      setCurrentPhraseIdx(0);
      setResult(null);
      setError(null);
      setQualityWarning(null);
    } catch (err) {
      setError(err.message || 'Failed to reset session');
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setError(null);
      setQualityWarning(null);
    }
  };

  const handleUploadClip = async () => {
    if (!selectedFile || !activeSession) return;

    setUploading(true);
    setError(null);
    setQualityWarning(null);

    try {
      const res = await sendSessionClip(activeSession.session_id, selectedFile);
      setUploading(false);
      setSelectedFile(null);

      if (res.quality_rejected) {
        setQualityWarning(`Audio Quality Gate Warning: ${res.reason}. Please re-record/upload clip for the same phrase.`);
        return;
      }

      if (res.session_completed && res.enroll_result) {
        setResult(res.enroll_result);
        setActiveSession(null);
        return;
      }

      if (res.next_phrase_index !== undefined) {
        setCurrentPhraseIdx(res.next_phrase_index);
      }
    } catch (err) {
      setUploading(false);
      setError(err.message || 'Failed to upload clip');
    }
  };

  const isHoldout = currentPhraseIdx >= 20;

  return (
    <div className="enroll-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Single-Session Enrollment Mode</h1>
          <p className="page-subtitle">Pretrained ECAPA-TDNN frozen voiceprint model generator</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          {activeSession && (
            <button className="btn-secondary" onClick={handleResetSession}>
              Reset Session
            </button>
          )}
          <button className="btn-secondary" onClick={() => navigate('/')}>
            Back to Dashboard
          </button>
        </div>
      </div>

      <div className="enroll-container">
        {!activeSession && !result ? (
          <form className="enroll-form" onSubmit={handleStartSession}>
            <div className="form-group">
              <label htmlFor="speakerId" className="form-label">
                Speaker ID
              </label>
              <input
                type="text"
                id="speakerId"
                className="form-input"
                value={speakerId}
                onChange={(e) => setSpeakerId(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="roomTag" className="form-label">
                Device / Room Tag (Provenance Tracking)
              </label>
              <input
                type="text"
                id="roomTag"
                className="form-input"
                placeholder="e.g. bedroom-laptop-mic"
                value={roomTag}
                onChange={(e) => setRoomTag(e.target.value)}
                required
              />
              <span className="form-hint">
                Captures sitting, room acoustic environment, and hardware microphone metadata.
              </span>
            </div>

            {error && (
              <div className="error-box">
                <p>{error}</p>
              </div>
            )}

            <button type="submit" className="btn-submit">
              Start Enrollment Session
            </button>
          </form>
        ) : activeSession && !result ? (
          <div className="enroll-session-card">
            <div className="session-info-bar" style={{ marginBottom: '20px', padding: '12px', background: '#f8fafc', borderRadius: '8px' }}>
              <div><strong>Session ID:</strong> {activeSession.session_id}</div>
              <div><strong>Device:</strong> {activeSession.device_name}</div>
              <div><strong>Room Tag:</strong> {activeSession.room_tag}</div>
            </div>

            <div className={`phrase-card ${isHoldout ? 'holdout' : 'enrollment'}`} style={{ border: isHoldout ? '2px solid #f59e0b' : '2px solid #3b82f6', padding: '20px', borderRadius: '12px', marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span className="badge" style={{ background: isHoldout ? '#fef3c7' : '#dbeafe', color: isHoldout ? '#92400e' : '#1e40af', padding: '4px 12px', borderRadius: '16px', fontWeight: 'bold' }}>
                  {isHoldout ? `HOLDOUT TEST CLIP (${currentPhraseIdx - 19}/2)` : `ENROLLMENT CLIP (${currentPhraseIdx + 1}/20)`}
                </span>
                <span className="step-counter">Phrase {currentPhraseIdx + 1} of 22</span>
              </div>
              <h2 style={{ fontSize: '1.4rem', margin: '15px 0' }}>"{SCRIPTED_PHRASES[currentPhraseIdx]}"</h2>
              {isHoldout && (
                <p style={{ color: '#b45309', fontSize: '0.9rem' }}>
                  Note: This clip is used exclusively for post-session verification and will NOT be averaged into the master voiceprint.
                </p>
              )}
            </div>

            {qualityWarning && (
              <div className="warning-box" style={{ background: '#fffbe0', border: '1px solid #ffe58f', padding: '12px', borderRadius: '8px', marginBottom: '15px', color: '#873800' }}>
                <strong>Quality Warning:</strong> {qualityWarning}
              </div>
            )}

            {error && (
              <div className="error-box" style={{ marginBottom: '15px' }}>
                <p>{error}</p>
              </div>
            )}

            <div className="upload-section">
              <input
                type="file"
                accept=".wav,.webm"
                onChange={handleFileSelect}
                className="form-input"
                style={{ marginBottom: '15px' }}
              />
              <button
                className="btn-primary"
                onClick={handleUploadClip}
                disabled={!selectedFile || uploading}
                style={{ width: '100%' }}
              >
                {uploading ? 'Processing & Verifying Quality...' : `Submit Clip ${currentPhraseIdx + 1}`}
              </button>
            </div>
          </div>
        ) : (
          <div className="enroll-results-card">
            <div className="success-icon-container">
              <svg className="success-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <polyline points="20 6 9 17 4 12" strokeWidth="3" strokeLinecap="round"/>
              </svg>
            </div>
            <h2 className="results-title">Enrollment & Holdout Verification Complete!</h2>

            <div className="stats-section">
              <div className="stats-grid">
                <div className="stat-card">
                  <span className="stat-value">{result.kept_count}</span>
                  <span className="stat-label">Kept Enrollment Clips</span>
                </div>
                <div className="stat-card">
                  <span className="stat-value">{result.dropped ? result.dropped.length : 0}</span>
                  <span className="stat-label">Inconsistent Dropped</span>
                </div>
                <div className="stat-card">
                  <span className="stat-value">{result.mean_similarity ? result.mean_similarity.toFixed(3) : 'N/A'}</span>
                  <span className="stat-label">Mean Cohesion</span>
                </div>
              </div>

              {result.holdout_results && (
                <div className="stats-details" style={{ marginTop: '25px' }}>
                  <h3>Holdout Verification Results (Independent Test)</h3>
                  <table className="stats-table">
                    <thead>
                      <tr>
                        <th>Clip ID</th>
                        <th>Cosine Similarity</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.holdout_results.map((h, i) => (
                        <tr key={i}>
                          <td>{h.sample_id}</td>
                          <td className="value">{h.score.toFixed(3)}</td>
                          <td>
                            <span style={{
                              padding: '4px 10px',
                              borderRadius: '12px',
                              fontWeight: 'bold',
                              color: h.passed ? '#15803d' : '#b91c1c',
                              background: h.passed ? '#dcfce7' : '#fee2e2'
                            }}>
                              {h.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <button className="btn-primary" style={{ marginTop: '20px' }} onClick={() => navigate('/')}>
              Go to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
