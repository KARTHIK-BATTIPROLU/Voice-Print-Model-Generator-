# Implementation Plan: VoicePrint Voice Biometric Platform

## Overview

This implementation plan follows a 4-stage approach to build a fully local voice biometric platform using Python/FastAPI for the backend and React/Vite for the frontend. The system uses SpeechBrain's ECAPA-TDNN model for speaker embedding extraction and cosine similarity for verification. All processing happens locally with zero cloud dependencies.

**Architecture:** Backend (Python/FastAPI) ↔ REST API + WebSocket ↔ Frontend (React/Vite)

**Key Technologies:**
- Backend: FastAPI, PyTorch, SpeechBrain, torchaudio, numpy
- Frontend: React 18, Vite, Web Audio API, custom CSS
- Storage: File-based (numpy .npy + JSON)

## Tasks

### Stage 1: Backend Core

- [x] 1. Set up backend project structure and dependencies
  - Create backend directory with Python virtual environment
  - Create requirements.txt with FastAPI, SpeechBrain, PyTorch, torchaudio, numpy, uvicorn, python-multipart, ffmpeg-python
  - Set up basic FastAPI app in `backend/main.py` with CORS middleware
  - Create module structure: `backend/model.py`, `backend/audio_utils.py`, `backend/embedding.py`, `backend/profile_store.py`
  - Create `backend/config.py` for application configuration
  - _Requirements: 8.2, 11.3_

- [x] 2. Implement Model Loader with singleton pattern
  - [x] 2.1 Create ModelLoader class in `backend/model.py`
    - Implement singleton pattern using class-level variable and threading.Lock()
    - Implement `get_instance()` static method with lazy loading
    - Load SpeechBrain ECAPA-TDNN model: `speechbrain/spkrec-ecapa-voxceleb`
    - Implement `is_loaded()` static method for health checks
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [ ]* 2.2 Write property test for Model Singleton Pattern
    - **Property 16: Model Singleton Pattern**
    - **Validates: Requirements 4.1, 4.5**
    - Test that multiple calls to `get_instance()` return same object (identity check with `is`)
    - Use Hypothesis to generate sequences of concurrent calls
    - _Requirements: 4.1, 4.5_

- [ ] 3. Implement Audio Processing utilities
  - [x] 3.1 Create audio validation function in `backend/audio_utils.py`
    - Implement `validate_wav(file_path)` with RIFF header checking
    - Return validation result dict with sample_rate, channels, duration, error
    - Validate sample rate range: 8kHz - 48kHz
    - Validate minimum duration: 1.5 seconds
    - Enforce maximum file size: 50MB
    - _Requirements: 1.2, 5.1, 5.3, 5.4_
  
  - [ ]* 3.2 Write property test for WAV Format Validation
    - **Property 5: WAV Format Validation**
    - **Validates: Requirements 1.2, 5.3**
    - Generate valid/invalid WAV files using Hypothesis strategies
    - Test that validation correctly identifies valid WAV files with RIFF headers
    - _Requirements: 1.2, 5.3_
  
  - [ ]* 3.3 Write property test for Sample Rate Validation
    - **Property 18: Sample Rate Validation**
    - **Validates: Requirements 5.1**
    - Generate WAV files with sample rates from [1000, 96000] Hz
    - Test that files are accepted iff sample rate in [8000, 48000] Hz
    - _Requirements: 5.1_
  
  - [x] 3.4 Create audio preprocessing functions
    - Implement `resample_audio(waveform, orig_sr, target_sr=16000)` using torchaudio
    - Implement `convert_to_mono(waveform)` for stereo to mono conversion
    - Implement `estimate_snr(waveform, sample_rate)` for SNR estimation in dB
    - Implement `segment_audio(waveform, sample_rate, segment_length=10.0)` for long audio
    - Implement `load_and_preprocess(file_path)` to orchestrate full pipeline
    - _Requirements: 1.3, 1.4, 1.5, 5.2, 5.6, 5.7_
  
  - [ ]* 3.5 Write property test for Audio Resampling
    - **Property 3: Audio Resampling Preserves Validity**
    - **Validates: Requirements 1.3, 2.4, 5.7**
    - Generate WAV files with sample rates in [8000, 48000] Hz
    - Test that resampling produces 16kHz mono audio with valid amplitude range [-1, 1]
    - Verify no NaN or infinite values after resampling
    - _Requirements: 1.3, 2.4, 5.7_
  
  - [ ]* 3.6 Write property test for Stereo to Mono Conversion
    - **Property 19: Stereo to Mono Conversion**
    - **Validates: Requirements 5.2**
    - Generate stereo audio waveforms (2 channels)
    - Test that conversion produces 1 channel with duration equal to original (±0.01s)
    - _Requirements: 5.2_
  
  - [ ]* 3.7 Write property test for Audio Segmentation
    - **Property 20: Audio Segmentation Correctness**
    - **Validates: Requirements 5.6**
    - Generate audio of various durations with segment length L
    - Test that segmentation produces ⌈D/L⌉ segments
    - Verify all segments except last have duration L seconds (±0.01s)
    - _Requirements: 5.6_

- [ ] 4. Implement Embedding Engine
  - [~] 4.1 Create embedding extraction in `backend/embedding.py`
    - Implement `extract_embedding(waveform, sample_rate)` using ModelLoader
    - Return 192-dimensional numpy array
    - Implement `normalize_embedding(embedding)` with L2 normalization
    - Implement `average_embeddings(embeddings)` for element-wise mean
    - _Requirements: 1.6, 1.7, 1.8, 2.5, 2.6_
  
  - [ ]* 4.2 Write property test for Embedding Extraction
    - **Property 1: Embedding Extraction Produces Valid Vectors**
    - **Validates: Requirements 1.6, 2.5**
    - Generate valid audio waveforms (≥1.5s, 16kHz)
    - Test that embedding extraction produces 192-dimensional numpy arrays
    - _Requirements: 1.6, 2.5_
  
  - [ ]* 4.3 Write property test for L2 Normalization
    - **Property 2: L2 Normalization Produces Unit Vectors**
    - **Validates: Requirements 1.7, 2.6**
    - Generate random embedding vectors
    - Test that L2 normalization produces vectors with L2 norm = 1.0 (±1e-6)
    - _Requirements: 1.7, 2.6_
  
  - [ ]* 4.4 Write property test for Voiceprint Averaging
    - **Property 6: Voiceprint Averaging Correctness**
    - **Validates: Requirements 1.8**
    - Generate collections of L2-normalized embeddings
    - Test that averaged voiceprint equals element-wise mean
    - _Requirements: 1.8_
  
  - [~] 4.5 Create similarity and statistics functions
    - Implement `compute_cosine_similarity(embedding_a, embedding_b)` as dot product
    - Implement `detect_outliers(embeddings, threshold=2.5)` using z-score method
    - Implement `compute_intra_class_stats(embeddings)` for mean, std, min, max similarity
    - _Requirements: 1.9, 1.10, 2.7, 3.2, 9.3_
  
  - [ ]* 4.6 Write property test for Cosine Similarity Computation
    - **Property 7: Cosine Similarity Computation**
    - **Validates: Requirements 2.7, 3.2, 9.3**
    - Generate pairs of L2-normalized embedding vectors
    - Test that cosine similarity equals dot product of A and B
    - _Requirements: 2.7, 3.2, 9.3_
  
  - [ ]* 4.7 Write property test for Cosine Similarity Identity
    - **Property 8: Cosine Similarity Identity Property**
    - **Validates: Requirements 9.6**
    - Generate valid voiceprint embeddings
    - Test that similarity(E, E) = 1.0 (±1e-6)
    - _Requirements: 9.6_
  
  - [ ]* 4.8 Write property test for Cosine Similarity Commutativity
    - **Property 9: Cosine Similarity Commutativity**
    - **Validates: Requirements 9.7**
    - Generate pairs of embedding vectors
    - Test that similarity(A, B) = similarity(B, A)
    - _Requirements: 9.7_
  
  - [ ]* 4.9 Write property test for Intra-Class Statistics
    - **Property 15: Intra-Class Statistics Computation**
    - **Validates: Requirements 1.9**
    - Generate collections of embeddings
    - Test that computed stats correctly reflect pairwise similarities
    - Verify mean, std, min, max calculations
    - _Requirements: 1.9_

- [ ] 5. Implement Profile Store
  - [~] 5.1 Create ProfileStore class in `backend/profile_store.py`
    - Implement `__init__(base_path="profiles")` to set base directory
    - Implement `create_profile(name, voiceprint, metadata)` with atomic write
    - Write voiceprint to `.npy` file and metadata to `meta.json`
    - Implement `get_profile(name)` to load voiceprint and metadata
    - Implement `list_profiles()` to return all profiles with metadata
    - Implement `delete_profile(name)` to remove profile directory
    - Implement `update_threshold(name, threshold)` to modify metadata
    - Implement `profile_exists(name)` for existence check
    - _Requirements: 1.11, 1.12, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [ ]* 5.2 Write property test for Voiceprint Persistence Round-Trip
    - **Property 11: Voiceprint Persistence Round-Trip**
    - **Validates: Requirements 1.11**
    - Generate valid voiceprint embedding arrays
    - Test that saving to .npy then loading produces equal array (tolerance 1e-7)
    - _Requirements: 1.11_
  
  - [ ]* 5.3 Write property test for Metadata JSON Round-Trip
    - **Property 12: Metadata JSON Round-Trip**
    - **Validates: Requirements 1.12**
    - Generate valid ProfileMetadata objects
    - Test that JSON serialize → deserialize preserves all fields
    - _Requirements: 1.12_
  
  - [ ]* 5.4 Write property test for Profile Threshold Round-Trip
    - **Property 17: Profile Threshold Configuration Round-Trip**
    - **Validates: Requirements 6.6, 9.5**
    - Generate threshold values in [0.0, 1.0]
    - Test that updating threshold to T then retrieving returns T
    - _Requirements: 6.6, 9.5_
  
  - [ ]* 5.5 Write property test for Profile Deletion Cleanup
    - **Property 21: Profile Deletion Cleanup**
    - **Validates: Requirements 6.5, 6.9**
    - Create profiles then delete them
    - Test that profile directory and files no longer exist after deletion
    - _Requirements: 6.5, 6.9_

- [ ] 6. Implement API routes
  - [~] 6.1 Create enrollment endpoint in `backend/main.py`
    - Implement `POST /api/enroll` with multipart form data
    - Accept profile_name and 10-500 WAV files
    - Process files: validate, resample, extract embeddings, average, detect outliers
    - Create profile with ProfileStore
    - Return EnrollmentResult JSON with stats
    - _Requirements: 1.1, 1.2, 1.3, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12_
  
  - [ ]* 6.2 Write property test for Enrollment File Count Validation
    - **Property 4: Enrollment File Count Validation**
    - **Validates: Requirements 1.1**
    - Generate enrollment requests with N files where N in [1, 600]
    - Test that request accepted iff 10 ≤ N ≤ 500
    - _Requirements: 1.1_
  
  - [~] 6.3 Create verification endpoints
    - Implement `POST /api/verify` for single audio verification
    - Accept profile_name and audio file
    - Extract embedding, compute similarity, apply threshold
    - Return VerificationResult JSON with score and pass/fail
    - Implement `POST /api/verify/batch` for multiple files
    - Return BatchVerificationResult with all scores and summary stats
    - _Requirements: 2.1, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 3.1, 3.2, 3.3_
  
  - [ ]* 6.4 Write property test for Threshold Comparison Logic
    - **Property 10: Threshold Comparison Logic**
    - **Validates: Requirements 2.8**
    - Generate similarity scores and thresholds
    - Test that verification passes iff score ≥ threshold
    - _Requirements: 2.8_
  
  - [ ]* 6.5 Write property test for Batch Verification Processes All Files
    - **Property 26: Batch Verification Processes All Files**
    - **Validates: Requirements 3.1**
    - Generate batch verification with N files
    - Test that results contain exactly N entries with matching filenames
    - _Requirements: 3.1_
  
  - [~] 6.6 Create profile management endpoints
    - Implement `GET /api/profiles` to list all profiles
    - Implement `GET /api/profiles/{name}` to get single profile
    - Implement `DELETE /api/profiles/{name}` to delete profile
    - Implement `PATCH /api/profiles/{name}/threshold` to update threshold
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_
  
  - [~] 6.7 Create health check endpoint
    - Implement `GET /api/health` endpoint
    - Check model loaded status using ModelLoader.is_loaded()
    - Return profile count and system uptime
    - _Requirements: 4.4_

- [~] 7. Checkpoint - Backend Core Complete
  - Run all backend tests (unit + property tests)
  - Verify model loads successfully
  - Test enrollment with sample WAV files
  - Test verification with enrolled profile
  - Ensure all tests pass, ask the user if questions arise

### Stage 2: Frontend

- [x] 8. Set up frontend project structure
  - Create frontend directory with `npm create vite@latest`
  - Choose React + JavaScript template
  - Install dependencies: none required (vanilla React)
  - Create directory structure: `src/pages/`, `src/components/`, `src/api/`, `src/styles/`
  - Set up CSS custom properties for design system in `src/styles/variables.css`
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.3_

- [x] 9. Implement Design System
  - [x] 9.1 Create CSS custom properties
    - Define color palette: background #0A0A0F, accent #6C63FF, success #00D9A3, error #FF6B6B
    - Define typography: Space Grotesk (display), Inter (body), JetBrains Mono (mono)
    - Define spacing scale: xs (4px) through 2xl (48px)
    - Set up component styles: border-radius, shadows, transitions
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 9.2 Create shared components
    - Create `ProfileCard.jsx` component with name, stats, action buttons
    - Create `ProgressRing.jsx` SVG component for circular progress
    - Create `ScoreGauge.jsx` SVG component for semicircle gauge with color gradient
    - Create `WaveformRing.jsx` component using Web Audio API AnalyserNode
    - _Requirements: 7.6, 7.7, 2.2, 3.3_

- [~] 10. Implement API Client
  - Create `src/api/api.js` with all API functions
  - Implement profile management: `getProfiles()`, `getProfile(name)`, `deleteProfile(name)`, `updateProfileThreshold(name, threshold)`
  - Implement enrollment: `enrollProfile(name, files, onProgress)`
  - Implement verification: `verifyLive(profileName, audioBlob)`, `verifyBatch(profileName, files)`
  - Implement health: `getHealth()`
  - Implement WebSocket: `connectProgressWebSocket(sessionId, onProgress, onComplete)`
  - Add error handling with retry logic (max 3 attempts)
  - Add timeout handling: 30s for enrollment, 10s for verification
  - _Requirements: 8.4, 8.7_

- [~] 11. Implement Dashboard page
  - Create `src/pages/Dashboard.jsx`
  - Fetch profiles using `getProfiles()` on mount
  - Display profile grid (1/2/3 columns responsive)
  - Render ProfileCard for each profile with name, sample count, creation date, stats
  - Add action buttons: "Verify Live", "Verify Batch", "Delete"
  - Add health indicator in header using `getHealth()`
  - Show empty state when no profiles exist
  - _Requirements: 6.7, 6.8, 7.10_

- [~] 12. Implement Enroll page
  - Create `src/pages/Enroll.jsx`
  - Add profile name input with validation (alphanumeric + allowed chars)
  - Add folder upload button (accept .wav files)
  - Display file count (must be 10-500)
  - Show ProgressRing during enrollment
  - Call `enrollProfile()` with files
  - Display enrollment summary on completion: samples processed/rejected, outliers, stats
  - Handle errors with user-friendly messages
  - _Requirements: 1.1, 7.6, 7.7, 10.2, 10.9_

- [~] 13. Implement Verify Live page
  - Create `src/pages/VerifyLive.jsx`
  - Add profile selector dropdown populated from `getProfiles()`
  - Implement microphone capture using Web Audio API
  - Display WaveformRing with real-time visualization using AnalyserNode
  - Add record button with visual feedback
  - Show recording timer during capture
  - Call `verifyLive()` after recording completes
  - Display ScoreGauge with similarity score
  - Show pass/fail indicator with color coding
  - _Requirements: 2.1, 2.2, 2.9, 2.10, 7.8_

- [ ] 14. Implement Verify Batch page
  - Create `src/pages/VerifyBatch.jsx`
  - Add profile selector dropdown
  - Add multi-file upload for batch verification
  - Add threshold slider (0.0 - 1.0) with live client-side updates
  - Call `verifyBatch()` with files
  - Display sortable table: Filename, Score, Status columns
  - Implement client-side sorting by clicking column headers
  - Color-code pass/fail rows
  - Add CSV export button
  - Display summary statistics: pass rate, mean score, std dev
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 7.9_
  
  - [ ]* 14.1 Write property test for Client-Side Threshold Update
    - **Property 22: Client-Side Threshold Update**
    - **Validates: Requirements 3.5**
    - Generate batch results with threshold T1, then update to T2
    - Test that pass/fail recalculated without changing similarity scores
    - Use fast-check in JavaScript/Jest
    - _Requirements: 3.5_
  
  - [ ]* 14.2 Write property test for CSV Round-Trip
    - **Property 13: Batch Results CSV Round-Trip**
    - **Validates: Requirements 3.6, 3.7**
    - Generate batch verification results, export to CSV, parse CSV
    - Test that parsed data structure equals original (filenames, scores, status)
    - _Requirements: 3.6, 3.7_

- [~] 15. Implement routing and navigation
  - Create `src/App.jsx` with React Router
  - Set up routes: `/` (Dashboard), `/enroll`, `/verify/live`, `/verify/batch`
  - Create navigation header with links to all pages
  - Add active route highlighting
  - Ensure keyboard navigation works for all routes
  - _Requirements: 7.10, 7.11_

- [~] 16. Checkpoint - Frontend Complete
  - Run frontend dev server with `npm run dev`
  - Test all pages render correctly
  - Verify design system colors and typography
  - Test responsive design down to 375px width
  - Ensure keyboard accessibility for all interactive elements
  - Ensure all tests pass, ask the user if questions arise

### Stage 3: Integration

- [ ] 17. Implement WebSocket progress streaming
  - [~] 17.1 Add WebSocket endpoint in backend
    - Implement `WebSocket /ws/progress/{session_id}` in `backend/main.py`
    - Send progress messages: `{"type": "progress", "current": int, "total": int, "percentage": float}`
    - Send completion message: `{"type": "complete", "success": bool, "result": dict}`
    - _Requirements: 1.13, 8.5_
  
  - [~] 17.2 Integrate WebSocket in enrollment
    - Modify enrollment endpoint to trigger WebSocket for >30 files
    - Connect WebSocket in `Enroll.jsx` during upload
    - Update ProgressRing with real-time percentage
    - _Requirements: 1.13, 8.5_

- [~] 18. Implement WebM to WAV conversion
  - Add ffmpeg-python to backend requirements
  - Create conversion utility in `backend/audio_utils.py`
  - Implement `convert_webm_to_wav(webm_path)` function
  - Integrate into `/api/verify` endpoint for browser-recorded audio
  - Handle conversion errors gracefully
  - _Requirements: 2.3, 8.6_

- [ ] 19. Implement CSV export functionality
  - Create CSV formatting function in `src/pages/VerifyBatch.jsx`
  - Format: `Filename,Score,Threshold,Verified,Timestamp`
  - Add download trigger using Blob and URL.createObjectURL
  - Test CSV opens correctly in spreadsheet applications
  - _Requirements: 3.6_
  
  - [ ]* 19.1 Write property test for Configuration Round-Trip
    - **Property 14: Configuration Round-Trip**
    - **Validates: Requirements 12.4**
    - Generate valid Configuration objects
    - Test that JSON formatting → parsing preserves all fields
    - _Requirements: 12.4_

- [~] 20. Create unified start script
  - Create `start.sh` bash script in project root
  - Start backend: `cd backend && uvicorn main:app --reload --port 8000`
  - Start frontend: `cd frontend && npm run dev`
  - Use `&` to run both in background
  - Add trap to kill both processes on Ctrl+C
  - _Requirements: 8.1_

- [~] 21. Configure CORS and API integration
  - Add CORS middleware to FastAPI in `backend/main.py`
  - Allow origins: `http://localhost:5173` (Vite dev server)
  - Allow methods: GET, POST, DELETE, PATCH
  - Allow headers: Content-Type, Authorization
  - Test API calls from frontend to backend
  - _Requirements: 8.8_

- [~] 22. Implement threshold override endpoint
  - Implement profile-specific threshold in verification
  - Modify `/api/verify` to check profile metadata for custom threshold
  - Fall back to default threshold (0.7) if not set
  - Test threshold override with different profiles
  - _Requirements: 9.4, 9.5_

- [~] 23. Checkpoint - Integration Complete
  - Start both servers using `start.sh`
  - Test complete enrollment flow: upload → progress → result
  - Test live verification: record → verify → result
  - Test batch verification: upload → results → CSV export
  - Test threshold updates from Dashboard
  - Verify WebSocket progress updates appear
  - Ensure all tests pass, ask the user if questions arise

### Stage 4: Hardening

- [ ] 24. Implement comprehensive error handling
  - [~] 24.1 Add validation error handlers
    - "Invalid audio format" for non-WAV files
    - "Minimum 10 samples required" for insufficient enrollment
    - "Audio must be at least 1.5 seconds" for short duration
    - "Profile not found" for missing profiles
    - "File size exceeds maximum" for large files
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [~] 24.2 Add system error handlers
    - "Model initialization failed" for model loading errors
    - Generic error messages for unexpected failures
    - Log detailed errors server-side only
    - Sanitize error responses to avoid information disclosure
    - _Requirements: 10.6, 10.7_
  
  - [~] 24.3 Add resource management
    - Release temporary resources after batch verification
    - Implement proper cleanup in all endpoints
    - Add request timeouts: 300s enrollment, 30s verification
    - _Requirements: 11.6_

- [~] 25. Implement input validation and security
  - Add profile name validation: regex `^[a-zA-Z0-9_-]{1,64}$`
  - Add path traversal prevention in ProfileStore
  - Validate threshold range: [0.0, 1.0]
  - Add NaN/Inf detection in audio processing
  - Validate file size before processing: 50MB max
  - _Requirements: 10.8, 10.9_

- [ ] 26. Implement performance optimizations
  - Verify model loaded once at startup (singleton)
  - Batch process embeddings when multiple samples provided
  - Use efficient numpy operations for similarity computation
  - Implement lazy loading for large profile lists in frontend
  - Add debounce to threshold slider in VerifyBatch (300ms)
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [ ]* 26.1 Write property test for Thread-Safe Concurrent Access
    - **Property 25: Thread-Safe Concurrent Model Access**
    - **Validates: Requirements 4.3, 4.5**
    - Generate N concurrent embedding extraction requests
    - Test that all complete successfully without errors
    - Verify all use same model instance
    - _Requirements: 4.3, 4.5_

- [ ] 27. Implement format and rate invariance tests
  - [ ]* 27.1 Write property test for Format Invariance
    - **Property 23: Format Invariance for Embeddings**
    - **Validates: Requirements 13.6**
    - Generate audio sample, create stereo and mono versions
    - Extract embeddings from both
    - Test that cosine similarity ≥ 0.95
    - _Requirements: 13.6_
  
  - [ ]* 27.2 Write property test for Sample Rate Invariance
    - **Property 24: Sample Rate Invariance for Embeddings**
    - **Validates: Requirements 13.7**
    - Generate audio at different source rates (8-48kHz)
    - Resample all to 16kHz, extract embeddings
    - Test that pairwise similarities ≥ 0.95
    - _Requirements: 13.7_

- [~] 28. Add accessibility improvements
  - Add ARIA labels to all interactive elements
  - Ensure focus indicators visible on all buttons and inputs
  - Add keyboard shortcuts: Enter to submit forms, Esc to close modals
  - Test screen reader compatibility with NVDA/JAWS
  - Verify color contrast meets WCAG AA: 4.5:1 for text
  - Add form input labels for all fields
  - _Requirements: 7.10, 7.11_

- [~] 29. Write end-to-end integration tests
  - Test complete enrollment: 50 WAV files → profile created
  - Test live verification: enroll → verify with same speaker
  - Test batch verification: enroll → batch verify → CSV export
  - Test error scenarios: invalid format, insufficient samples, profile not found
  - Test model behavior: same-speaker >0.8, different-speaker <0.5
  - Verify zero cloud dependencies: disconnect network, test all features
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 9.1, 9.2_

- [~] 30. Final checkpoint and documentation
  - Run full test suite: all unit tests, property tests (100 iterations), integration tests
  - Verify all error messages match error handling matrix
  - Test responsive design on mobile (375px) and desktop (1920px)
  - Create README.md with setup instructions, architecture overview, API documentation
  - Document configuration options in config.py
  - Test start.sh script on clean environment
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional property-based test tasks and can be skipped for faster MVP
- All property tests use Hypothesis (Python backend) or fast-check (JavaScript frontend)
- Property tests validate universal correctness properties across random inputs
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at major milestones
- Model loading happens once at startup for efficiency (singleton pattern)
- All processing is local - zero cloud or network dependencies
- CORS configured for local development (frontend: 5173, backend: 8000)
- Profile storage uses simple file system: `profiles/{name}/[voiceprint.npy, meta.json]`

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1", "8"]
    },
    {
      "id": 1,
      "tasks": ["2.1", "9.1"]
    },
    {
      "id": 2,
      "tasks": ["2.2", "3.1", "9.2"]
    },
    {
      "id": 3,
      "tasks": ["3.2", "3.3", "3.4", "10"]
    },
    {
      "id": 4,
      "tasks": ["3.5", "3.6", "3.7", "4.1", "11"]
    },
    {
      "id": 5,
      "tasks": ["4.2", "4.3", "4.4", "4.5", "12"]
    },
    {
      "id": 6,
      "tasks": ["4.6", "4.7", "4.8", "4.9", "5.1", "13"]
    },
    {
      "id": 7,
      "tasks": ["5.2", "5.3", "5.4", "5.5", "6.1", "14"]
    },
    {
      "id": 8,
      "tasks": ["6.2", "6.3", "14.1", "14.2"]
    },
    {
      "id": 9,
      "tasks": ["6.4", "6.5", "6.6", "6.7", "15"]
    },
    {
      "id": 10,
      "tasks": ["17.1"]
    },
    {
      "id": 11,
      "tasks": ["17.2", "18", "19"]
    },
    {
      "id": 12,
      "tasks": ["19.1", "20", "21", "22"]
    },
    {
      "id": 13,
      "tasks": ["24.1", "24.2", "24.3"]
    },
    {
      "id": 14,
      "tasks": ["25", "26"]
    },
    {
      "id": 15,
      "tasks": ["26.1", "27.1", "27.2"]
    },
    {
      "id": 16,
      "tasks": ["28", "29"]
    },
    {
      "id": 17,
      "tasks": ["30"]
    }
  ]
}
```
