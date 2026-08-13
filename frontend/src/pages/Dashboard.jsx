import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProfiles, deleteProfile } from '../api/api';
import { ProfileCard } from '../components';
import './Dashboard.css';

export default function Dashboard() {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const fetchProfiles = async () => {
    setLoading(true);
    try {
      const data = await getProfiles();
      setProfiles(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load profiles');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfiles();
  }, []);

  const handleVerifyLive = (name) => {
    navigate(`/verify-live?profile=${encodeURIComponent(name)}`);
  };

  const handleVerifyBatch = (name) => {
    navigate(`/verify-batch?profile=${encodeURIComponent(name)}`);
  };

  const handleDelete = async (name) => {
    try {
      await deleteProfile(name);
      setProfiles((prev) => prev.filter((p) => p.name !== name));
    } catch (err) {
      alert(`Error deleting profile: ${err.message}`);
    }
  };

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Voice Print Profiles</h1>
          <p className="page-subtitle">Manage enrolled speakers, configure thresholds, and run biometrics.</p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/enroll')}>
          Enroll Voice Print
        </button>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading biometric profiles...</p>
        </div>
      ) : error ? (
        <div className="error-alert">
          <svg className="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10" strokeWidth="2"/>
            <line x1="12" y1="8" x2="12" y2="12" strokeWidth="2"/>
            <line x1="12" y1="16" x2="12.01" y2="16" strokeWidth="2"/>
          </svg>
          <div>
            <h3>Error loading profiles</h3>
            <p>{error}</p>
          </div>
          <button className="btn-retry" onClick={fetchProfiles}>Retry</button>
        </div>
      ) : profiles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon-container">
            <svg className="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" strokeWidth="2"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" strokeWidth="2"/>
            </svg>
          </div>
          <h2>No Profiles Enrolled</h2>
          <p>Get started by enrolling a new voice print profile. You will need to provide at least 10 short WAV audio recordings of their voice.</p>
          <button className="btn-primary" onClick={() => navigate('/enroll')}>
            Enroll First Voice Print
          </button>
        </div>
      ) : (
        <div className="profiles-grid">
          {profiles.map((profile) => (
            <ProfileCard
              key={profile.name}
              name={profile.name}
              sampleCount={profile.metadata.sample_count || 0}
              createdAt={profile.metadata.created}
              threshold={profile.metadata.threshold || 0.7}
              intraClassStats={profile.metadata.intra_class_stats}
              onVerifyLive={handleVerifyLive}
              onVerifyBatch={handleVerifyBatch}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
