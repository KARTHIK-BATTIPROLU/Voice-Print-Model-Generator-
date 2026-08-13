import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getProfiles, verifyBatch } from '../api/api';
import './VerifyBatch.css';

export default function VerifyBatch() {
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  // Interactive threshold state
  const [threshold, setThreshold] = useState(0.7);
  
  // Sorting state
  const [sortBy, setSortBy] = useState('filename');
  const [sortOrder, setSortOrder] = useState('asc');

  const navigate = useNavigate();
  const location = useLocation();

  // Load profiles and parse query param
  useEffect(() => {
    const fetchProfiles = async () => {
      try {
        const data = await getProfiles();
        setProfiles(data);
        
        const params = new URLSearchParams(location.search);
        const profileParam = params.get('profile');
        if (profileParam && data.some((p) => p.name === profileParam)) {
          setSelectedProfile(profileParam);
          const prof = data.find((p) => p.name === profileParam);
          setThreshold(prof.metadata.threshold || 0.7);
        } else if (data.length > 0) {
          setSelectedProfile(data[0].name);
          setThreshold(data[0].metadata.threshold || 0.7);
        }
      } catch (err) {
        setError('Failed to fetch speaker profiles: ' + err.message);
      }
    };
    fetchProfiles();
  }, [location]);

  // Adjust threshold if profile changes
  const handleProfileChange = (profileName) => {
    setSelectedProfile(profileName);
    const prof = profiles.find((p) => p.name === profileName);
    if (prof) {
      setThreshold(prof.metadata.threshold || 0.7);
    }
    setResult(null);
    setError(null);
  };

  const handleFileChange = (e) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedProfile) {
      setError('Please select a profile first');
      return;
    }
    if (selectedFiles.length === 0) {
      setError('Please select at least one file to verify');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await verifyBatch(selectedProfile, selectedFiles);
      setResult(data);
      // Synchronize threshold from results initially
      const prof = profiles.find((p) => p.name === selectedProfile);
      setThreshold(prof ? (prof.metadata.threshold || 0.7) : 0.7);
    } catch (err) {
      setError(err.message || 'Batch verification failed');
    } finally {
      setLoading(false);
    }
  };

  // Dynamic calculations based on sliding threshold
  const getDynamicResults = () => {
    if (!result || !result.results) return [];
    
    return result.results.map((item) => {
      if (item.error) {
        return { ...item, dynamicVerified: false };
      }
      return {
        ...item,
        dynamicVerified: item.similarity_score >= threshold
      };
    });
  };

  const getDynamicSummary = (dynamicResults) => {
    if (dynamicResults.length === 0) return null;
    
    const validScores = dynamicResults
      .filter((r) => !r.error)
      .map((r) => r.similarity_score);
      
    const passedCount = dynamicResults.filter((r) => r.dynamicVerified).length;
    const total = dynamicResults.length;
    
    // Mean
    const mean = validScores.length
      ? validScores.reduce((a, b) => a + b, 0) / validScores.length
      : 0.0;
      
    // Standard deviation
    const variance = validScores.length
      ? validScores.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / validScores.length
      : 0.0;
    const stdDev = Math.sqrt(variance);

    return {
      total,
      passed: passedCount,
      failed: total - passedCount,
      passRate: passedCount / total,
      mean,
      stdDev
    };
  };

  // Sort function
  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const getSortedResults = (dynamicResults) => {
    return [...dynamicResults].sort((a, b) => {
      let valA, valB;
      
      if (sortBy === 'filename') {
        valA = a.filename.toLowerCase();
        valB = b.filename.toLowerCase();
      } else if (sortBy === 'score') {
        valA = a.error ? -1 : a.similarity_score;
        valB = b.error ? -1 : b.similarity_score;
      } else if (sortBy === 'status') {
        valA = a.dynamicVerified ? 1 : 0;
        valB = b.dynamicVerified ? 1 : 0;
      }
      
      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  };

  const exportToCSV = () => {
    if (!result) return;
    const dynamicResults = getDynamicResults();
    
    let csvContent = 'data:text/csv;charset=utf-8,';
    csvContent += 'Filename,SimilarityScore,Threshold,Verified,Error\r\n';
    
    dynamicResults.forEach((item) => {
      const score = item.error ? 0.0 : item.similarity_score;
      const errorMsg = item.error ? `"${item.error.replace(/"/g, '""')}"` : 'None';
      csvContent += `"${item.filename}",${score.toFixed(4)},${threshold.toFixed(2)},${item.dynamicVerified},${errorMsg}\r\n`;
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `batch_verify_${selectedProfile}_threshold_${threshold.toFixed(2)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const dynamicResults = getDynamicResults();
  const dynamicSummary = getDynamicSummary(dynamicResults);
  const sortedResults = getSortedResults(dynamicResults);

  return (
    <div className="verify-batch-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Batch Voice Verification</h1>
          <p className="page-subtitle">Verify multiple audio files and dynamically analyze thresholds.</p>
        </div>
        <button className="btn-secondary" onClick={() => navigate('/')}>
          Back to Dashboard
        </button>
      </div>

      <div className="verify-batch-container">
        <form className="verify-batch-form" onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group flex-1">
              <label htmlFor="profileSelect" className="form-label">
                Speaker Profile
              </label>
              <select
                id="profileSelect"
                className="form-select"
                value={selectedProfile}
                onChange={(e) => handleProfileChange(e.target.value)}
                disabled={loading}
              >
                {profiles.map((p) => (
                  <option key={p.name} value={p.name}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group flex-1">
              <label className="form-label">Select Audio Files</label>
              <div className="file-input-wrapper">
                <input
                  type="file"
                  id="batchFiles"
                  multiple
                  accept=".wav,.webm"
                  className="file-input-hidden"
                  onChange={handleFileChange}
                  disabled={loading}
                />
                <label htmlFor="batchFiles" className="btn-file-select">
                  Browse Files
                </label>
                <span className="file-count-label">
                  {selectedFiles.length === 0
                    ? 'No files selected'
                    : `${selectedFiles.length} files selected`}
                </span>
              </div>
            </div>
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
            disabled={loading || selectedFiles.length === 0 || !selectedProfile}
          >
            {loading ? 'Running Verification...' : 'Run Batch Verification'}
          </button>
        </form>

        {loading && (
          <div className="batch-loading-state">
            <div className="spinner"></div>
            <p>Processing files, extracting embeddings, and validating scores...</p>
          </div>
        )}

        {result && dynamicSummary && (
          <div className="batch-results-section">
            <div className="threshold-analyzer-panel">
              <div className="panel-header">
                <h3>Interactive Threshold Optimizer</h3>
                <span className="info-badge">Slide to adjust threshold dynamically</span>
              </div>
              <div className="slider-container">
                <input
                  type="range"
                  min="0.4"
                  max="0.95"
                  step="0.01"
                  value={threshold}
                  onChange={(e) => setThreshold(parseFloat(e.target.value))}
                  className="threshold-range-slider"
                />
                <div className="slider-value-display">
                  <span>Current Threshold: <strong>{threshold.toFixed(2)}</strong></span>
                </div>
              </div>
            </div>

            <div className="summary-dashboard">
              <div className="stat-card passed">
                <span className="stat-value">{dynamicSummary.passed}</span>
                <span className="stat-label">Passed Files</span>
              </div>
              <div className="stat-card failed">
                <span className="stat-value">{dynamicSummary.failed}</span>
                <span className="stat-label">Failed Files</span>
              </div>
              <div className="stat-card rate">
                <span className="stat-value">
                  {(dynamicSummary.passRate * 100).toFixed(1)}%
                </span>
                <span className="stat-label">Pass Rate</span>
              </div>
              <div className="stat-card mean">
                <span className="stat-value">{dynamicSummary.mean.toFixed(4)}</span>
                <span className="stat-label">Mean Score</span>
              </div>
            </div>

            <div className="results-table-card">
              <div className="table-actions">
                <h4>Verification Logs</h4>
                <button className="btn-csv-export" onClick={exportToCSV}>
                  Export CSV
                </button>
              </div>

              <div className="table-wrapper">
                <table className="results-table">
                  <thead>
                    <tr>
                      <th onClick={() => handleSort('filename')}>
                        Filename {sortBy === 'filename' && (sortOrder === 'asc' ? '▲' : '▼')}
                      </th>
                      <th onClick={() => handleSort('score')} className="text-right">
                        Similarity {sortBy === 'score' && (sortOrder === 'asc' ? '▲' : '▼')}
                      </th>
                      <th onClick={() => handleSort('status')} className="text-center">
                        Status {sortBy === 'status' && (sortOrder === 'asc' ? '▲' : '▼')}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedResults.map((item, idx) => (
                      <tr
                        key={idx}
                        className={
                          item.error
                            ? 'row-error'
                            : item.dynamicVerified
                            ? 'row-passed'
                            : 'row-failed'
                        }
                      >
                        <td className="cell-filename" title={item.filename}>
                          {item.filename}
                        </td>
                        <td className="cell-score text-right">
                          {item.error ? (
                            <span className="error-text" title={item.error}>
                              Error
                            </span>
                          ) : (
                            item.similarity_score.toFixed(4)
                          )}
                        </td>
                        <td className="cell-status text-center">
                          {item.error ? (
                            <span className="status-pill error">REJECTED</span>
                          ) : item.dynamicVerified ? (
                            <span className="status-pill passed">PASSED</span>
                          ) : (
                            <span className="status-pill failed">FAILED</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
