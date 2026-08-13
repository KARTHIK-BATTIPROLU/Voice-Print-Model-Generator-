import { useState } from 'react';
import './ProfileCard.css';

/**
 * ProfileCard Component
 * 
 * Displays profile information with action buttons for verification and deletion.
 * 
 * @param {Object} props
 * @param {string} props.name - Profile name
 * @param {number} props.sampleCount - Number of enrollment samples
 * @param {string} props.createdAt - ISO8601 creation timestamp
 * @param {number} props.threshold - Verification threshold (0.0-1.0)
 * @param {Object} props.intraClassStats - Intra-class similarity statistics
 * @param {Function} props.onVerifyLive - Callback for live verification
 * @param {Function} props.onVerifyBatch - Callback for batch verification
 * @param {Function} props.onDelete - Callback for deletion
 */
export default function ProfileCard({
  name,
  sampleCount,
  createdAt,
  threshold,
  intraClassStats,
  onVerifyLive,
  onVerifyBatch,
  onDelete
}) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Format date to readable format
  const formatDate = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = () => {
    setShowDeleteConfirm(false);
    onDelete(name);
  };

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
  };

  return (
    <div className="profile-card">
      <div className="profile-card-header">
        <h3 className="profile-card-name">{name}</h3>
        <span className="profile-card-badge">{sampleCount} samples</span>
      </div>

      <div className="profile-card-info">
        <div className="profile-info-item">
          <span className="profile-info-label">Created</span>
          <span className="profile-info-value">{formatDate(createdAt)}</span>
        </div>

        <div className="profile-info-item">
          <span className="profile-info-label">Threshold</span>
          <span className="profile-info-value">{threshold.toFixed(2)}</span>
        </div>

        {intraClassStats && intraClassStats.mean_similarity && (
          <div className="profile-info-item">
            <span className="profile-info-label">Mean Similarity</span>
            <span className="profile-info-value">
              {intraClassStats.mean_similarity.toFixed(3)}
            </span>
          </div>
        )}
      </div>

      {!showDeleteConfirm ? (
        <div className="profile-card-actions">
          <button
            className="profile-action-btn primary"
            onClick={() => onVerifyLive(name)}
          >
            Verify Live
          </button>
          <button
            className="profile-action-btn secondary"
            onClick={() => onVerifyBatch(name)}
          >
            Test Batch
          </button>
          <button
            className="profile-action-btn danger"
            onClick={handleDeleteClick}
          >
            Delete
          </button>
        </div>
      ) : (
        <div className="profile-card-confirm">
          <p className="confirm-message">Delete this profile?</p>
          <div className="confirm-actions">
            <button
              className="confirm-btn cancel"
              onClick={handleCancelDelete}
            >
              Cancel
            </button>
            <button
              className="confirm-btn delete"
              onClick={handleConfirmDelete}
            >
              Delete
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
