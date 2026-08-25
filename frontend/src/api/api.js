/**
 * API Client for VoicePrint Frontend
 * Centralized API communication layer with retry logic and error handling
 * Validates: Requirements 8.4, 8.7
 */

const getApiHost = () => {
  const envUrl = import.meta.env?.VITE_API_URL;
  if (envUrl) return envUrl.replace(/\/$/, '');
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return window.location.origin;
  }
  return 'http://localhost:8000';
};

const API_HOST = getApiHost();
const API_BASE_URL = `${API_HOST}/api`;
const WS_BASE_URL = `${API_HOST.replace(/^http/, 'ws')}/ws/progress`;

// Timeout configurations
const TIMEOUTS = {
  enrollment: 30000,  // 30 seconds for enrollment
  verification: 10000, // 10 seconds for verification
  default: 15000      // 15 seconds default
};

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second base delay

/**
 * Sleep utility for retry delays with exponential backoff
 * @param {number} ms - Base delay in milliseconds
 * @param {number} attempt - Current attempt number (for exponential backoff)
 */
const sleep = (ms, attempt = 0) => 
  new Promise(resolve => setTimeout(resolve, ms * Math.pow(2, attempt)));

/**
 * Custom error class for API errors
 */
class APIError extends Error {
  constructor(message, status, response) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.response = response;
  }
}

/**
 * Fetch with timeout support
 * @param {string} url - Request URL
 * @param {object} options - Fetch options
 * @param {number} timeout - Timeout in milliseconds
 * @returns {Promise<Response>}
 */
async function fetchWithTimeout(url, options = {}, timeout = TIMEOUTS.default) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new APIError('Request timeout', 408, null);
    }
    throw error;
  }
}

/**
 * Make API request with automatic retry logic
 * @param {string} url - Request URL
 * @param {object} options - Fetch options
 * @param {number} timeout - Timeout in milliseconds
 * @param {number} maxRetries - Maximum retry attempts
 * @returns {Promise<object>}
 */
async function apiRequest(url, options = {}, timeout = TIMEOUTS.default, maxRetries = MAX_RETRIES) {
  let lastError;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetchWithTimeout(url, options, timeout);
      
      // Parse JSON response
      const data = await response.json();
      
      // Handle HTTP errors
      if (!response.ok) {
        throw new APIError(
          data.error || data.detail || `HTTP ${response.status}`,
          response.status,
          data
        );
      }
      
      return data;
    } catch (error) {
      lastError = error;
      
      // Don't retry on client errors (4xx) except timeout
      if (error instanceof APIError && error.status >= 400 && error.status < 500 && error.status !== 408) {
        throw error;
      }
      
      // Don't retry on the last attempt
      if (attempt < maxRetries - 1) {
        await sleep(RETRY_DELAY, attempt);
        console.log(`Retry attempt ${attempt + 1} for ${url}`);
      }
    }
  }
  
  // All retries failed
  throw lastError || new APIError('Request failed after retries', 0, null);
}

/**
 * Profile Management Functions
 */

/**
 * Get all profiles
 * @returns {Promise<Array>} Array of profile objects
 */
export async function getProfiles() {
  try {
    const data = await apiRequest(`${API_BASE_URL}/profiles`);
    return data.profiles || [];
  } catch (error) {
    console.error('Failed to fetch profiles:', error);
    throw new Error(error.message || 'Failed to fetch profiles');
  }
}

/**
 * Get a single profile by name
 * @param {string} name - Profile name
 * @returns {Promise<object>} Profile object
 */
export async function getProfile(name) {
  try {
    const data = await apiRequest(`${API_BASE_URL}/profiles/${encodeURIComponent(name)}`);
    if (!data.exists) {
      throw new Error('Profile not found');
    }
    return {
      name: data.name,
      ...data.metadata
    };
  } catch (error) {
    console.error(`Failed to fetch profile ${name}:`, error);
    throw new Error(error.message || `Failed to fetch profile ${name}`);
  }
}

/**
 * Delete a profile
 * @param {string} name - Profile name
 * @returns {Promise<boolean>} True if deleted successfully
 */
export async function deleteProfile(name) {
  try {
    const data = await apiRequest(
      `${API_BASE_URL}/profiles/${encodeURIComponent(name)}`,
      { method: 'DELETE' }
    );
    
    if (!data.success || !data.deleted) {
      throw new Error(data.error || 'Failed to delete profile');
    }
    
    return true;
  } catch (error) {
    console.error(`Failed to delete profile ${name}:`, error);
    throw new Error(error.message || `Failed to delete profile ${name}`);
  }
}

/**
 * Update profile threshold
 * @param {string} name - Profile name
 * @param {number} threshold - New threshold value (0.0 - 1.0)
 * @returns {Promise<boolean>} True if updated successfully
 */
export async function updateProfileThreshold(name, threshold) {
  // Validate threshold range
  if (threshold < 0 || threshold > 1) {
    throw new Error('Threshold must be between 0.0 and 1.0');
  }
  
  try {
    const data = await apiRequest(
      `${API_BASE_URL}/profiles/${encodeURIComponent(name)}/threshold`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ threshold })
      }
    );
    
    if (!data.success || !data.updated) {
      throw new Error(data.error || 'Failed to update threshold');
    }
    
    return true;
  } catch (error) {
    console.error(`Failed to update threshold for ${name}:`, error);
    throw new Error(error.message || `Failed to update threshold for ${name}`);
  }
}

/**
 * Single-Session Enrollment API Functions
 */

export async function startSession(roomTag = 'bedroom-laptop-mic', speakerId = 'ASTA_primary') {
  const formData = new FormData();
  formData.append('room_tag', roomTag);
  if (speakerId) formData.append('speaker_id', speakerId);

  return await apiRequest(
    `${API_BASE_URL}/session/start`,
    {
      method: 'POST',
      body: formData
    }
  );
}

export async function getSessionStatus() {
  return await apiRequest(`${API_BASE_URL}/session/status`);
}

export async function resetSession() {
  return await apiRequest(
    `${API_BASE_URL}/session/reset`,
    { method: 'POST' }
  );
}

export async function sendSessionClip(sessionId, audioFile) {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  formData.append('audio_file', audioFile, 'recording.wav');

  return await apiRequest(
    `${API_BASE_URL}/session/clip`,
    {
      method: 'POST',
      body: formData
    },
    TIMEOUTS.enrollment
  );
}

export async function stopSession(sessionId) {
  const formData = new FormData();
  formData.append('session_id', sessionId);

  return await apiRequest(
    `${API_BASE_URL}/session/stop`,
    {
      method: 'POST',
      body: formData
    },
    TIMEOUTS.enrollment
  );
}

/**
 * Enrollment Functions
 */


/**
 * Enroll a new profile with voice samples
 * @param {string} name - Profile name
 * @param {File[]} files - Array of WAV audio files (10-500)
 * @param {Function} onProgress - Progress callback (optional)
 * @returns {Promise<object>} Enrollment result
 */
export async function enrollProfile(name, files, onProgress = null) {
  // Validate input
  if (!name || typeof name !== 'string') {
    throw new Error('Profile name is required');
  }
  
  if (!Array.isArray(files) || files.length < 10 || files.length > 500) {
    throw new Error('Minimum 10 and maximum 500 samples required for enrollment');
  }
  
  // Create FormData
  const formData = new FormData();
  formData.append('profile_name', name);
  
  for (const file of files) {
    formData.append('files', file);
  }
  
  try {
    // For large enrollments (>30 files), use WebSocket for progress
    const useWebSocket = files.length > 30 && onProgress;
    const sessionId = useWebSocket ? generateSessionId() : null;
    
    if (sessionId) {
      formData.append('session_id', sessionId);
    }
    
    // Connect WebSocket before starting enrollment
    let wsConnection = null;
    if (useWebSocket) {
      wsConnection = connectProgressWebSocket(
        sessionId,
        onProgress,
        () => { /* handled by main promise */ }
      );
    }
    
    // Make enrollment request
    const data = await apiRequest(
      `${API_BASE_URL}/enroll`,
      {
        method: 'POST',
        body: formData
      },
      TIMEOUTS.enrollment
    );
    
    // Close WebSocket if opened
    if (wsConnection) {
      wsConnection.close();
    }
    
    if (!data.success) {
      throw new Error(data.error || 'Enrollment failed');
    }
    
    return {
      success: true,
      profileName: data.profile_name,
      samplesProcessed: data.samples_processed,
      samplesRejected: data.samples_rejected,
      outliers: data.outliers_detected || [],
      stats: data.intra_class_stats || {}
    };
  } catch (error) {
    console.error('Enrollment failed:', error);
    throw new Error(error.message || 'Enrollment failed');
  }
}

/**
 * Verification Functions
 */

/**
 * Verify identity using live audio recording
 * @param {string} profileName - Profile name to verify against
 * @param {Blob} audioBlob - Audio blob from microphone
 * @returns {Promise<object>} Verification result
 */
export async function verifyLive(profileName, audioBlob) {
  if (!profileName || typeof profileName !== 'string') {
    throw new Error('Profile name is required');
  }
  
  if (!audioBlob || !(audioBlob instanceof Blob)) {
    throw new Error('Audio blob is required');
  }
  
  try {
    // Create FormData
    const formData = new FormData();
    formData.append('profile_name', profileName);
    formData.append('audio_file', audioBlob, 'recording.wav');
    
    // Make verification request
    const data = await apiRequest(
      `${API_BASE_URL}/verify`,
      {
        method: 'POST',
        body: formData
      },
      TIMEOUTS.verification
    );
    
    if (!data.success) {
      throw new Error(data.error || 'Verification failed');
    }
    
    return {
      success: true,
      profileName: data.profile_name,
      similarityScore: data.similarity_score,
      threshold: data.threshold,
      verified: data.verified
    };
  } catch (error) {
    console.error('Live verification failed:', error);
    throw new Error(error.message || 'Live verification failed');
  }
}

/**
 * Verify multiple audio files against a profile (batch verification)
 * @param {string} profileName - Profile name to verify against
 * @param {File[]} files - Array of audio files
 * @returns {Promise<object>} Batch verification results
 */
export async function verifyBatch(profileName, files) {
  if (!profileName || typeof profileName !== 'string') {
    throw new Error('Profile name is required');
  }
  
  if (!Array.isArray(files) || files.length === 0) {
    throw new Error('At least one audio file is required');
  }
  
  try {
    // Create FormData
    const formData = new FormData();
    formData.append('profile_name', profileName);
    
    for (const file of files) {
      formData.append('files', file);
    }
    
    // Make batch verification request
    const data = await apiRequest(
      `${API_BASE_URL}/verify/batch`,
      {
        method: 'POST',
        body: formData
      },
      TIMEOUTS.verification * 2 // Allow more time for batch
    );
    
    if (!data.success) {
      throw new Error(data.error || 'Batch verification failed');
    }
    
    return {
      success: true,
      profileName: data.profile_name,
      results: data.results || [],
      summary: data.summary || null
    };
  } catch (error) {
    console.error('Batch verification failed:', error);
    throw new Error(error.message || 'Batch verification failed');
  }
}

/**
 * System Health Functions
 */

/**
 * Get system health status
 * @returns {Promise<object>} Health status
 */
export async function getHealth() {
  try {
    const data = await apiRequest(`${API_BASE_URL}/health`, {}, 5000); // 5 second timeout
    
    return {
      status: data.status,
      modelLoaded: data.model_loaded,
      profileCount: data.profile_count,
      uptime: data.uptime
    };
  } catch (error) {
    console.error('Health check failed:', error);
    return {
      status: 'unhealthy',
      modelLoaded: false,
      profileCount: 0,
      uptime: 0,
      error: error.message
    };
  }
}

/**
 * WebSocket Functions
 */

/**
 * Generate a unique session ID for WebSocket connection
 * @returns {string} Session ID
 */
function generateSessionId() {
  return `session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Connect to progress WebSocket
 * @param {string} sessionId - Session ID for this connection
 * @param {Function} onProgress - Progress callback (current, total, percentage, message)
 * @param {Function} onComplete - Completion callback (success, result)
 * @returns {WebSocket} WebSocket connection
 */
export function connectProgressWebSocket(sessionId, onProgress, onComplete) {
  const wsUrl = `${WS_BASE_URL}/${sessionId}`;
  const ws = new WebSocket(wsUrl);
  
  ws.onopen = () => {
    console.log(`WebSocket connected: ${sessionId}`);
  };
  
  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data);
      
      if (message.type === 'progress') {
        if (onProgress && typeof onProgress === 'function') {
          onProgress({
            current: message.current,
            total: message.total,
            percentage: message.percentage,
            message: message.message
          });
        }
      } else if (message.type === 'complete') {
        if (onComplete && typeof onComplete === 'function') {
          onComplete({
            success: message.success,
            result: message.result
          });
        }
        ws.close();
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  ws.onclose = () => {
    console.log(`WebSocket closed: ${sessionId}`);
  };
  
  return ws;
}

/**
 * Export error class for external use
 */
export { APIError };
