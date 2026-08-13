import { useState, useEffect, useRef } from 'react'
import ProfileCard from './components/ProfileCard'
import WaveformRing from './components/WaveformRing'
import ScoreGauge from './components/ScoreGauge'
import ProgressRing from './components/ProgressRing'
import './App.css'

const API = 'http://localhost:8000'

// ─── tiny helpers ────────────────────────────────────────────────
function StatusDot({ ok }) {
  return (
    <span style={{
      display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
      background: ok ? 'var(--success)' : 'var(--error)',
      boxShadow: ok ? '0 0 6px var(--success)' : '0 0 6px var(--error)',
      marginRight: 6
    }} />
  )
}

function TabBtn({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '8px 20px', borderRadius: 6, fontWeight: 600, fontSize: 14,
        background: active ? 'var(--accent)' : 'var(--surface)',
        color: active ? '#fff' : 'var(--text-secondary)',
        border: active ? '2px solid var(--accent)' : '2px solid var(--border)',
        cursor: 'pointer', transition: 'all .2s'
      }}
    >{children}</button>
  )
}

// ─── main app ────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState('enroll')          // 'enroll' | 'verify' | 'profiles'
  const [apiStatus, setApiStatus] = useState(null)
  const [profiles, setProfiles] = useState([])
  const [toast, setToast] = useState(null)

  // enroll state
  const [enrollName, setEnrollName] = useState('')
  const [enrollFile, setEnrollFile] = useState(null)
  const [enrolling, setEnrolling] = useState(false)
  const [enrollProgress, setEnrollProgress] = useState(0)

  // verify state
  const [verifyFile, setVerifyFile] = useState(null)
  const [verifyProfile, setVerifyProfile] = useState('')
  const [verifying, setVerifying] = useState(false)
  const [verifyResult, setVerifyResult] = useState(null)

  // recording state
  const [recording, setRecording] = useState(false)
  const [audioStream, setAudioStream] = useState(null)
  const [recordedBlob, setRecordedBlob] = useState(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  // ── poll health ──────────────────────────────────────────────
  useEffect(() => {
    const check = () =>
      fetch(`${API}/api/health`)
        .then(r => r.json())
        .then(d => setApiStatus(d))
        .catch(() => setApiStatus(null))
    check()
    const id = setInterval(check, 5000)
    return () => clearInterval(id)
  }, [])

  // ── load profiles ────────────────────────────────────────────
  const loadProfiles = () =>
    fetch(`${API}/api/profiles`)
      .then(r => r.ok ? r.json() : [])
      .then(d => setProfiles(Array.isArray(d) ? d : d.profiles || []))
      .catch(() => setProfiles([]))

  useEffect(() => { loadProfiles() }, [])

  // ── toast helper ────────────────────────────────────────────
  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }

  // ── microphone recording ─────────────────────────────────────
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      setAudioStream(stream)
      chunksRef.current = []
      const mr = new MediaRecorder(stream)
      mr.ondataavailable = e => chunksRef.current.push(e.data)
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setRecordedBlob(blob)
        stream.getTracks().forEach(t => t.stop())
        setAudioStream(null)
      }
      mr.start()
      mediaRecorderRef.current = mr
      setRecording(true)
    } catch {
      showToast('Microphone access denied', 'error')
    }
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    setRecording(false)
  }

  // ── enroll ───────────────────────────────────────────────────
  const handleEnroll = async () => {
    const audioSource = enrollFile || (recordedBlob
      ? new File([recordedBlob], 'recording.webm', { type: 'audio/webm' })
      : null)

    if (!enrollName.trim()) return showToast('Enter a speaker name', 'error')
    if (!audioSource) return showToast('Upload or record audio', 'error')

    setEnrolling(true)
    setEnrollProgress(0)
    const tick = setInterval(() => setEnrollProgress(p => Math.min(p + 8, 85)), 200)

    const fd = new FormData()
    fd.append('name', enrollName.trim())
    fd.append('audio', audioSource)

    try {
      const r = await fetch(`${API}/api/enroll`, { method: 'POST', body: fd })
      clearInterval(tick)
      setEnrollProgress(100)
      if (r.ok) {
        const d = await r.json()
        showToast(`✓ Enrolled "${enrollName}" (${d.sample_count || 1} samples)`)
        setEnrollName('')
        setEnrollFile(null)
        setRecordedBlob(null)
        loadProfiles()
      } else {
        const e = await r.json().catch(() => ({}))
        showToast(e.detail || 'Enrollment failed', 'error')
      }
    } catch {
      clearInterval(tick)
      showToast('Cannot reach backend', 'error')
    } finally {
      setEnrolling(false)
      setTimeout(() => setEnrollProgress(0), 1000)
    }
  }

  // ── verify ───────────────────────────────────────────────────
  const handleVerify = async () => {
    const audioSource = verifyFile || (recordedBlob
      ? new File([recordedBlob], 'recording.webm', { type: 'audio/webm' })
      : null)

    if (!verifyProfile) return showToast('Select a speaker profile', 'error')
    if (!audioSource) return showToast('Upload or record audio', 'error')

    setVerifying(true)
    setVerifyResult(null)

    const fd = new FormData()
    fd.append('profile_name', verifyProfile)
    fd.append('audio', audioSource)

    try {
      const r = await fetch(`${API}/api/verify`, { method: 'POST', body: fd })
      if (r.ok) {
        const d = await r.json()
        setVerifyResult(d)
      } else {
        const e = await r.json().catch(() => ({}))
        showToast(e.detail || 'Verification failed', 'error')
      }
    } catch {
      showToast('Cannot reach backend', 'error')
    } finally {
      setVerifying(false)
    }
  }

  // ── delete profile ───────────────────────────────────────────
  const handleDelete = async (name) => {
    try {
      const r = await fetch(`${API}/api/profiles/${encodeURIComponent(name)}`, { method: 'DELETE' })
      if (r.ok) {
        showToast(`Deleted profile "${name}"`)
        loadProfiles()
      } else {
        showToast('Delete failed', 'error')
      }
    } catch {
      showToast('Cannot reach backend', 'error')
    }
  }

  // ─────────────────────────────────────────────────────────────
  return (
    <div className="vp-app">

      {/* ── HEADER ── */}
      <header className="vp-header">
        <div className="vp-logo">
          <span className="vp-logo-icon">🎙️</span>
          <span className="vp-logo-text">VoicePrint</span>
          <span className="vp-logo-sub">Speaker Recognition</span>
        </div>
        <div className="vp-status-bar">
          <StatusDot ok={!!apiStatus} />
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            {apiStatus ? `API online · uptime ${Math.floor(apiStatus.uptime)}s` : 'API offline'}
          </span>
          {apiStatus && (
            <span style={{ marginLeft: 12, fontSize: 13, color: 'var(--text-secondary)' }}>
              {profiles.length} profile{profiles.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </header>

      {/* ── TABS ── */}
      <nav className="vp-tabs">
        <TabBtn active={tab === 'enroll'}   onClick={() => setTab('enroll')}>🧬 Enroll</TabBtn>
        <TabBtn active={tab === 'verify'}   onClick={() => setTab('verify')}>🔍 Verify</TabBtn>
        <TabBtn active={tab === 'profiles'} onClick={() => setTab('profiles')}>👥 Profiles ({profiles.length})</TabBtn>
      </nav>

      {/* ── CONTENT ── */}
      <main className="vp-main">

        {/* ════ ENROLL TAB ════ */}
        {tab === 'enroll' && (
          <div className="vp-panel">
            <h2>Enroll a Speaker</h2>
            <p className="vp-hint">Record or upload a WAV/audio clip to register a voice print.</p>

            <label className="vp-label">Speaker Name</label>
            <input
              className="vp-input"
              placeholder="e.g. Alice"
              value={enrollName}
              onChange={e => setEnrollName(e.target.value)}
            />

            <div className="vp-audio-section">
              {/* Waveform */}
              <div className="vp-waveform-wrap">
                <WaveformRing audioStream={audioStream} size={180} isRecording={recording} />
                <div className="vp-record-btns">
                  {!recording
                    ? <button className="vp-btn primary" onClick={startRecording}>⏺ Record</button>
                    : <button className="vp-btn danger" onClick={stopRecording}>⏹ Stop</button>
                  }
                </div>
                {recordedBlob && !enrollFile && (
                  <span className="vp-badge success">Recording ready</span>
                )}
              </div>

              <div className="vp-divider">OR</div>

              {/* File upload */}
              <label className="vp-upload-box">
                <input
                  type="file"
                  accept="audio/*"
                  style={{ display: 'none' }}
                  onChange={e => { setEnrollFile(e.target.files[0]); setRecordedBlob(null) }}
                />
                <span className="vp-upload-icon">📂</span>
                <span>{enrollFile ? enrollFile.name : 'Upload audio file'}</span>
              </label>
            </div>

            {enrollProgress > 0 && (
              <div className="vp-progress-row">
                <ProgressRing percentage={enrollProgress} size={60} strokeWidth={6}
                  color={enrollProgress === 100 ? 'var(--success)' : 'var(--accent)'} />
                <span style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
                  {enrollProgress < 100 ? 'Enrolling…' : 'Done!'}
                </span>
              </div>
            )}

            <button
              className="vp-btn primary full"
              onClick={handleEnroll}
              disabled={enrolling}
            >
              {enrolling ? '⏳ Enrolling…' : '✅ Enroll Speaker'}
            </button>
          </div>
        )}

        {/* ════ VERIFY TAB ════ */}
        {tab === 'verify' && (
          <div className="vp-panel">
            <h2>Verify a Speaker</h2>
            <p className="vp-hint">Check if an audio clip matches an enrolled voice print.</p>

            <label className="vp-label">Compare Against Profile</label>
            <select
              className="vp-input"
              value={verifyProfile}
              onChange={e => setVerifyProfile(e.target.value)}
            >
              <option value="">— Select a profile —</option>
              {profiles.map(p => (
                <option key={p.name || p} value={p.name || p}>{p.name || p}</option>
              ))}
            </select>

            <div className="vp-audio-section">
              <div className="vp-waveform-wrap">
                <WaveformRing audioStream={audioStream} size={180} isRecording={recording} />
                <div className="vp-record-btns">
                  {!recording
                    ? <button className="vp-btn primary" onClick={startRecording}>⏺ Record</button>
                    : <button className="vp-btn danger" onClick={stopRecording}>⏹ Stop</button>
                  }
                </div>
                {recordedBlob && !verifyFile && (
                  <span className="vp-badge success">Recording ready</span>
                )}
              </div>

              <div className="vp-divider">OR</div>

              <label className="vp-upload-box">
                <input
                  type="file"
                  accept="audio/*"
                  style={{ display: 'none' }}
                  onChange={e => { setVerifyFile(e.target.files[0]); setRecordedBlob(null) }}
                />
                <span className="vp-upload-icon">📂</span>
                <span>{verifyFile ? verifyFile.name : 'Upload audio file'}</span>
              </label>
            </div>

            <button
              className="vp-btn primary full"
              onClick={handleVerify}
              disabled={verifying}
            >
              {verifying ? '⏳ Verifying…' : '🔍 Verify Speaker'}
            </button>

            {/* Result */}
            {verifyResult && (
              <div className={`vp-result ${verifyResult.verified ? 'match' : 'no-match'}`}>
                <div className="vp-result-top">
                  <span className="vp-result-verdict">
                    {verifyResult.verified ? '✅ MATCH' : '❌ NO MATCH'}
                  </span>
                  <span className="vp-result-profile">
                    vs. <strong>{verifyResult.profile_name || verifyProfile}</strong>
                  </span>
                </div>
                <ScoreGauge
                  score={verifyResult.similarity_score ?? verifyResult.score ?? 0}
                  threshold={verifyResult.threshold ?? 0.7}
                  size={220}
                />
                <div className="vp-result-details">
                  <div>Score: <strong>{((verifyResult.similarity_score ?? verifyResult.score ?? 0)).toFixed(4)}</strong></div>
                  <div>Threshold: <strong>{(verifyResult.threshold ?? 0.7).toFixed(2)}</strong></div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ════ PROFILES TAB ════ */}
        {tab === 'profiles' && (
          <div className="vp-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2>Enrolled Profiles</h2>
              <button className="vp-btn secondary" onClick={loadProfiles}>↻ Refresh</button>
            </div>

            {profiles.length === 0 ? (
              <div className="vp-empty">
                <span style={{ fontSize: 48 }}>🎙️</span>
                <p>No profiles enrolled yet.</p>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                  Go to the <strong>Enroll</strong> tab to add a speaker.
                </p>
              </div>
            ) : (
              <div className="vp-profiles-grid">
                {profiles.map(p => (
                  <ProfileCard
                    key={p.name || p}
                    name={p.name || p}
                    sampleCount={p.sample_count ?? p.sampleCount ?? 1}
                    createdAt={p.created_at ?? p.createdAt ?? new Date().toISOString()}
                    threshold={p.threshold ?? 0.7}
                    intraClassStats={p.intra_class_stats ?? p.intraClassStats}
                    onVerifyLive={name => { setVerifyProfile(name); setTab('verify') }}
                    onVerifyBatch={name => { setVerifyProfile(name); setTab('verify') }}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* ── TOAST ── */}
      {toast && (
        <div className={`vp-toast ${toast.type}`}>
          {toast.msg}
        </div>
      )}
    </div>
  )
}
