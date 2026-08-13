import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { enrollProfile } from '../api/api';
import { ProgressRing } from '../components';
import './Enroll.css';

export default function Enroll() {
  const [profileName, setProfileName] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMsg, setProgressMsg] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // Validate name using regex: alphanumeric, dashes, underscores
  const isNameValid = (name) => {
    const pattern = /^[a-zA-Z0-9_-]{1,64}$/;
    return pattern.test(name);
  };

  const handleFileChange = (e) => {
    if (e.target.files) {
      const filesArray = Array.from(e.target.files);
      // Filter out non-wav/webm files if necessary, but browser accept handles it
      setSelectedFiles(filesArray);
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!profileName) {
      setError('Profile name is required');
      return;
    }
    if (!isNameValid(profileName)) {
      setError('Profile name must be 1-64 characters and contain only letters, numbers, dashes (-), or underscores (_)');
      return;
    }
    if (selectedFiles.length < 10 || selectedFiles.length > 500) {
      setError(`Minimum 10 and maximum 500 files required. Selected: ${selectedFiles.length}`);
      return;
    }

    setUploading(true);
    setProgress(0);
    setProgressMsg('Uploading audio samples...');
    setError(null);
    setResult(null);

    try {
      const data = await enrollProfile(profileName, selectedFiles, (progressData) => {
        setProgress(progressData.percentage);
        setProgressMsg(progressData.message);
      });
      setResult(data);
      setUploading(false);
    } catch (err) {
      setError(err.message || 'Enrollment failed');
      setUploading(false);
    }
  };

  return (
    <div className="enroll-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Enroll Speaker Profile</h1>
          <p className="page-subtitle">Create a unique voice print by uploading 10-500 audio samples.</p>
        </div>
        <button className="btn-secondary" onClick={() => navigate('/')}>
          Back to Dashboard
        </button>
      </div>

      <div className="enroll-container">
        {!uploading && !result ? (
          <form className="enroll-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="profileName" className="form-label">
                Profile Name <span className="required">*</span>
              </label>
              <input
                type="text"
                id="profileName"
                className="form-input"
                placeholder="e.g. john_doe"
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
                disabled={uploading}
              />
              <span className="form-hint">
                Only alphanumeric characters, dashes (-), and underscores (_) are allowed. Maximum 64 characters.
              </span>
            </div>

            <div className="form-group">
              <label className="form-label">
                Voice Samples (WAV or WebM) <span className="required">*</span>
              </label>
              <div className="file-dropzone">
                <input
                  type="file"
                  id="audioFiles"
                  className="file-input-hidden"
                  multiple
                  accept=".wav,.webm"
                  onChange={handleFileChange}
                />
                <label htmlFor="audioFiles" className="file-dropzone-label">
                  <svg className="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" strokeWidth="2" strokeLinecap="round"/>
                    <polyline points="17 8 12 3 7 8" strokeWidth="2" strokeLinecap="round"/>
                    <line x1="12" y1="3" x2="12" y2="15" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                  <span>Select Audio Files</span>
                  <span className="file-type-hint">WAV / WebM (minimum 10 files)</span>
                </label>
              </div>

              {selectedFiles.length > 0 && (
                <div className="file-list-container">
                  <div className="file-list-header">
                    <span>Selected Files ({selectedFiles.length})</span>
                    <button
                      type="button"
                      className="btn-clear"
                      onClick={() => setSelectedFiles([])}
                    >
                      Clear
                    </button>
                  </div>
                  <ul className="file-list">
                    {selectedFiles.slice(0, 5).map((file, idx) => (
                      <li key={idx} className="file-item">
                        <span className="file-name">{file.name}</span>
                        <span className="file-size">
                          {(file.size / 1024).toFixed(1)} KB
                        </span>
                      </li>
                    ))}
                    {selectedFiles.length > 5 && (
                      <li className="file-item-more">
                        and {selectedFiles.length - 5} more files...
                      </li>
                    )}
                  </ul>
                </div>
              )}
            </div>

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

            <button
              type="submit"
              className="btn-submit"
              disabled={uploading || !profileName || selectedFiles.length < 10}
            >
              Start Enrollment
            </button>
          </form>
        ) : uploading ? (
          <div className="enroll-progress-card">
            <ProgressRing percentage={progress} size={160} strokeWidth={12} />
            <h2 className="progress-title">Enrolling "{profileName}"</h2>
            <p className="progress-msg">{progressMsg}</p>
          </div>
        ) : (
          <div className="enroll-results-card">
            <div className="success-icon-container">
              <svg className="success-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <polyline points="20 6 9 17 4 12" strokeWidth="3" strokeLinecap="round"/>
              </svg>
            </div>
            <h2 className="results-title">Enrollment Successful!</h2>
            <p className="results-subtitle">
              Voice print profile created successfully for <strong>{result.profileName}</strong>.
            </p>

            <div className="stats-section">
              <div className="stats-grid">
                <div className="stat-card">
                  <span className="stat-value">{result.samplesProcessed}</span>
                  <span className="stat-label">Samples Processed</span>
                </div>
                <div className="stat-card">
                  <span className="stat-value">{result.samplesRejected}</span>
                  <span className="stat-label">Samples Rejected</span>
                </div>
                <div className="stat-card">
                  <span className="stat-value">{result.outliers.length}</span>
                  <span className="stat-label">Outliers Filtered</span>
                </div>
              </div>

              {result.stats && result.stats.mean_similarity !== undefined && (
                <div className="stats-details">
                  <h3>Intra-Class Cohesion Statistics</h3>
                  <table className="stats-table">
                    <tbody>
                      <tr>
                        <td>Mean Similarity</td>
                        <td className="value">{result.stats.mean_similarity.toFixed(4)}</td>
                      </tr>
                      <tr>
                        <td>Std Deviation</td>
                        <td className="value">{result.stats.std_similarity.toFixed(4)}</td>
                      </tr>
                      <tr>
                        <td>Min Similarity</td>
                        <td className="value">{result.stats.min_similarity.toFixed(4)}</td>
                      </tr>
                      <tr>
                        <td>Max Similarity</td>
                        <td className="value">{result.stats.max_similarity.toFixed(4)}</td>
                      </tr>
                    </tbody>
                  </table>
                  <p className="stats-explanation">
                    Cohesion indicates how similar the enrollment samples are to each other. Higher similarity and lower standard deviation indicate a high-quality voice print.
                  </p>
                </div>
              )}
            </div>

            <button className="btn-primary" onClick={() => navigate('/')}>
              Go to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
