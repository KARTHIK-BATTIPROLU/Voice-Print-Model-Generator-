import { HashRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { getHealth } from './api/api';
import Dashboard from './pages/Dashboard';
import Enroll from './pages/Enroll';
import VerifyLive from './pages/VerifyLive';
import VerifyBatch from './pages/VerifyBatch';
import './App.css';

function App() {
  const [health, setHealth] = useState({
    status: 'checking',
    modelLoaded: false,
    profileCount: 0
  });

  const checkHealthStatus = async () => {
    try {
      const status = await getHealth();
      setHealth({
        status: status.status,
        modelLoaded: status.modelLoaded,
        profileCount: status.profileCount
      });
    } catch (err) {
      setHealth({
        status: 'offline',
        modelLoaded: false,
        profileCount: 0
      });
    }
  };

  useEffect(() => {
    checkHealthStatus();
    const interval = setInterval(checkHealthStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = () => {
    if (health.status === 'healthy') {
      return (
        <div className="system-status-indicator healthy" title="System is fully operational">
          <span className="status-dot"></span>
          <span className="status-label">Online</span>
        </div>
      );
    } else if (health.status === 'unhealthy') {
      return (
        <div className="system-status-indicator loading" title="Model is loading or unloaded">
          <span className="status-dot"></span>
          <span className="status-label">Model Unloaded</span>
        </div>
      );
    } else {
      return (
        <div className="system-status-indicator offline" title="Backend server cannot be reached">
          <span className="status-dot"></span>
          <span className="status-label">Offline</span>
        </div>
      );
    }
  };

  return (
    <Router>
      <header className="app-header">
        <div className="header-brand" onClick={() => window.location.href = '#/'}>
          <div className="logo-mark">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M12 2v20M17 5v14M22 9v6M7 7v10M2 10v4" strokeWidth="2.5" strokeLinecap="round"/>
            </svg>
          </div>
          <div className="brand-text">
            <h2>VoicePrint</h2>
            <span>Biometric Engine</span>
          </div>
        </div>

        <nav className="header-nav">
          <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Dashboard
          </NavLink>
          <NavLink to="/enroll" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Enroll
          </NavLink>
          <NavLink to="/verify-live" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Verify Live
          </NavLink>
          <NavLink to="/verify-batch" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Verify Batch
          </NavLink>
        </nav>

        <div className="header-status">
          {getStatusBadge()}
        </div>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/enroll" element={<Enroll />} />
          <Route path="/verify-live" element={<VerifyLive />} />
          <Route path="/verify-batch" element={<VerifyBatch />} />
        </Routes>
      </main>

      <footer className="app-footer">
        <p>© 2026 VoicePrint Local Biometric Authentication. All ML inference occurs offline.</p>
        <div className="footer-stats">
          <span>Active Profiles: <strong>{health.profileCount}</strong></span>
          <span>Model: <strong>ECAPA-TDNN (192-dim)</strong></span>
        </div>
      </footer>
    </Router>
  );
}

export default App;
