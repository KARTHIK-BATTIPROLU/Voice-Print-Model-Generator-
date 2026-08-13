# Requirements Document

## Introduction

VoicePrint is a full-stack, fully local, zero-cloud voice biometric platform for speaker enrollment and verification. The system enables users to create unique voiceprints from voice samples and verify speaker identity through real-time microphone input or batch audio file processing. The platform uses SpeechBrain's pretrained ECAPA-TDNN model for embedding extraction and cosine similarity scoring, with all processing occurring locally without cloud dependencies.

## Glossary

- **VoicePrint_System**: The complete voice biometric platform including backend API and frontend interface
- **Embedding_Engine**: Component responsible for extracting voice embeddings using ECAPA-TDNN model
- **Model_Loader**: Singleton component managing SpeechBrain ECAPA-TDNN model instance
- **Audio_Processor**: Component handling WAV validation, resampling, and segmentation
- **Profile_Store**: File-based persistence layer storing voiceprint embeddings and metadata
- **Voiceprint**: L2-normalized averaged embedding vector representing a speaker's voice characteristics
- **Enrollment**: Process of creating a voiceprint from multiple voice samples
- **Verification**: Process of comparing audio input against stored voiceprint using cosine similarity
- **Cosine_Similarity**: Metric measuring similarity between two embedding vectors (range: -1 to 1)
- **Threshold**: Configurable similarity score above which verification is considered successful
- **Profile**: User identity record containing voiceprint, metadata, and statistics
- **Dashboard**: Frontend view displaying all enrolled profiles with management actions
- **Enroll_Page**: Frontend interface for uploading voice samples and creating profiles
- **Verify_Live_Page**: Frontend interface for real-time microphone verification
- **Verify_Batch_Page**: Frontend interface for testing multiple audio files against a profile
- **Waveform_Ring**: Animated visualization element displaying audio input levels
- **SNR**: Signal-to-Noise Ratio measured in decibels
- **ECAPA_TDNN**: Emphasized Channel Attention, Propagation and Aggregation Time Delay Neural Network model

## Requirements

### Requirement 1: Voice Sample Enrollment

**User Story:** As a user, I want to upload multiple voice samples to generate a personal voiceprint, so that I can later verify my identity using my voice.

#### Acceptance Criteria

1. THE Enrollment_Endpoint SHALL accept between 10 and 500 WAV files per enrollment request
2. WHEN enrollment is initiated, THE Audio_Processor SHALL validate each WAV file for format compliance
3. FOR ALL valid WAV files, THE Audio_Processor SHALL resample audio to 16kHz mono format
4. WHEN a voice sample is shorter than 1.5 seconds, THE Audio_Processor SHALL reject the sample
5. WHEN a voice sample has SNR below 5dB, THE Audio_Processor SHALL filter out the sample
6. FOR ALL accepted samples, THE Embedding_Engine SHALL extract voice embeddings using ECAPA_TDNN model
7. THE Embedding_Engine SHALL apply L2 normalization to each extracted embedding
8. THE Embedding_Engine SHALL compute the averaged voiceprint from all normalized embeddings
9. THE Embedding_Engine SHALL calculate intra-class statistics for enrollment samples
10. THE Embedding_Engine SHALL detect and flag outlier samples in the enrollment set
11. THE Profile_Store SHALL persist the voiceprint as a numpy array file (voiceprint.npy)
12. THE Profile_Store SHALL persist profile metadata as JSON (meta.json) including creation timestamp and sample count
13. WHERE enrollment contains more than 30 files, THE VoicePrint_System SHALL provide WebSocket progress updates

### Requirement 2: Real-Time Microphone Verification

**User Story:** As a user, I want to verify my identity in real-time using my microphone, so that I can authenticate quickly without pre-recorded files.

#### Acceptance Criteria

1. THE Verify_Live_Page SHALL capture audio from the user's microphone
2. THE Verify_Live_Page SHALL display an animated Waveform_Ring that reacts to microphone volume
3. WHEN the user completes recording, THE Frontend SHALL convert WebM audio to WAV format
4. THE Audio_Processor SHALL resample the recorded audio to 16kHz mono format
5. THE Embedding_Engine SHALL extract voice embedding from the recorded audio
6. THE Embedding_Engine SHALL apply L2 normalization to the extracted embedding
7. THE Verification_Endpoint SHALL compute cosine similarity between recorded embedding and stored voiceprint
8. THE Verification_Endpoint SHALL compare the similarity score against the configured threshold
9. THE Verification_Endpoint SHALL return the similarity score and verification result (pass/fail)
10. THE Verify_Live_Page SHALL display the similarity score and verification status to the user

### Requirement 3: Batch Audio Verification

**User Story:** As a user, I want to test multiple audio clips against a saved voiceprint, so that I can evaluate verification accuracy across different samples.

#### Acceptance Criteria

1. THE Verify_Batch_Page SHALL accept multiple audio files for batch verification
2. FOR ALL uploaded audio files, THE Verification_Endpoint SHALL compute cosine similarity against the selected voiceprint
3. THE Verify_Batch_Page SHALL display verification scores in a sortable table format
4. THE Verify_Batch_Page SHALL provide a threshold slider for adjusting pass/fail criteria
5. WHEN the threshold slider is adjusted, THE Verify_Batch_Page SHALL update pass/fail results client-side without API calls
6. THE Verify_Batch_Page SHALL provide CSV export functionality for batch results
7. FOR ALL batch verification requests, parsing the CSV then reformatting SHALL produce an equivalent data structure (round-trip property)

### Requirement 4: Model Management

**User Story:** As a developer, I want the ECAPA-TDNN model loaded efficiently, so that the system performs well under concurrent requests.

#### Acceptance Criteria

1. THE Model_Loader SHALL implement singleton pattern to ensure only one model instance exists
2. WHEN the VoicePrint_System starts, THE Model_Loader SHALL load the SpeechBrain ECAPA_TDNN model
3. THE Model_Loader SHALL be thread-safe for concurrent access
4. THE Health_Check_Endpoint SHALL verify model availability and return system status
5. WHEN multiple embedding requests occur concurrently, THE Model_Loader SHALL serve all requests using the single model instance

### Requirement 5: Audio Processing Pipeline

**User Story:** As a system, I want to handle diverse audio inputs correctly, so that users can upload files from various sources and recording conditions.

#### Acceptance Criteria

1. THE Audio_Processor SHALL accept WAV files with sample rates between 8kHz and 48kHz
2. WHEN stereo audio is provided, THE Audio_Processor SHALL convert it to mono format
3. THE Audio_Processor SHALL validate WAV file headers and reject corrupted files
4. THE Audio_Processor SHALL enforce maximum file size limits to prevent resource exhaustion
5. WHEN audio processing fails, THE Audio_Processor SHALL return descriptive error messages
6. THE Audio_Processor SHALL segment long audio files if needed for processing
7. FOR ALL valid audio transformations, THE Audio_Processor SHALL preserve speech intelligibility

### Requirement 6: Profile Management

**User Story:** As a user, I want to manage my voice profiles, so that I can create, view, update, and delete my biometric data.

#### Acceptance Criteria

1. THE Profile_Store SHALL store each profile in a dedicated directory (profiles/{name}/)
2. THE Profile_Management_Endpoint SHALL support creating new profiles
3. THE Profile_Management_Endpoint SHALL support retrieving profile metadata
4. THE Profile_Management_Endpoint SHALL support listing all profiles
5. THE Profile_Management_Endpoint SHALL support deleting profiles
6. THE Profile_Management_Endpoint SHALL support updating profile threshold settings
7. THE Dashboard SHALL display all profiles in a grid layout with statistics
8. THE Dashboard SHALL provide action buttons for verification and deletion per profile
9. WHEN a profile is deleted, THE Profile_Store SHALL remove all associated files (voiceprint.npy and meta.json)

### Requirement 7: Frontend User Interface

**User Story:** As a user, I want an intuitive dark-themed interface, so that I can easily navigate enrollment and verification workflows.

#### Acceptance Criteria

1. THE Frontend SHALL use #0A0A0F as the background color
2. THE Frontend SHALL use #6C63FF (electric violet) as the accent color
3. THE Frontend SHALL use Space Grotesk font for display text
4. THE Frontend SHALL use Inter font for body text
5. THE Frontend SHALL use JetBrains Mono font for technical information
6. THE Enroll_Page SHALL display upload progress tracking during enrollment
7. THE Enroll_Page SHALL display enrollment summary upon completion
8. THE Verify_Live_Page SHALL use Web Audio API for real-time waveform visualization
9. THE Verify_Batch_Page SHALL display score table with color-coded pass/fail indicators
10. THE Frontend SHALL be responsive down to 375px width for mobile devices
11. THE Frontend SHALL be keyboard accessible for all interactive elements

### Requirement 8: System Integration

**User Story:** As a developer, I want seamless backend-frontend integration, so that the system operates as a unified platform.

#### Acceptance Criteria

1. THE VoicePrint_System SHALL provide a single start.sh script to launch both backend and frontend servers
2. THE Backend SHALL run on FastAPI framework with Python
3. THE Frontend SHALL run on React with Vite build tooling
4. THE Backend SHALL expose RESTful API endpoints for all operations
5. WHERE large enrollments occur, THE Backend SHALL use WebSocket protocol for progress streaming
6. THE Frontend SHALL handle WebM to WAV conversion for browser-recorded audio
7. THE API SHALL use JSON format for request and response payloads
8. THE API SHALL include appropriate CORS headers for frontend communication

### Requirement 9: Verification Accuracy

**User Story:** As a user, I want reliable verification results, so that I can trust the system's authentication decisions.

#### Acceptance Criteria

1. WHEN the same speaker is verified, THE VoicePrint_System SHALL produce similarity scores above 0.8
2. WHEN a different speaker is verified, THE VoicePrint_System SHALL produce similarity scores below 0.5
3. THE VoicePrint_System SHALL use cosine similarity as the scoring metric
4. THE Profile SHALL store a configurable threshold value (default: 0.7)
5. THE Verification_Endpoint SHALL support profile-specific threshold override
6. FOR ALL valid voiceprints, computing similarity with itself SHALL produce scores near 1.0 (identity property)
7. FOR ALL embedding pairs, cosine similarity SHALL be commutative: sim(A,B) equals sim(B,A)

### Requirement 10: Error Handling and Validation

**User Story:** As a user, I want clear error messages when operations fail, so that I can understand and correct issues.

#### Acceptance Criteria

1. WHEN invalid file format is uploaded, THE VoicePrint_System SHALL return "Invalid audio format" error
2. WHEN insufficient samples are provided for enrollment, THE VoicePrint_System SHALL return "Minimum 10 samples required" error
3. WHEN audio duration is too short, THE VoicePrint_System SHALL return "Audio must be at least 1.5 seconds" error
4. WHEN a non-existent profile is referenced, THE VoicePrint_System SHALL return "Profile not found" error
5. WHEN file size exceeds limits, THE VoicePrint_System SHALL return "File size exceeds maximum" error
6. WHEN model loading fails, THE VoicePrint_System SHALL return "Model initialization failed" error
7. IF an unexpected error occurs, THEN THE VoicePrint_System SHALL log the error and return a generic error message to the user
8. THE VoicePrint_System SHALL sanitize all user inputs to prevent injection attacks
9. THE VoicePrint_System SHALL validate profile names to contain only alphanumeric characters and allowed special characters

### Requirement 11: Performance and Resource Management

**User Story:** As a system administrator, I want efficient resource utilization, so that the platform runs smoothly on local hardware.

#### Acceptance Criteria

1. THE Model_Loader SHALL load the model once at startup rather than per request
2. THE VoicePrint_System SHALL process embeddings in batches when multiple samples are provided
3. THE Profile_Store SHALL use efficient file I/O operations for reading and writing embeddings
4. THE Frontend SHALL implement lazy loading for large profile lists
5. THE Frontend SHALL debounce user input in threshold sliders to reduce unnecessary re-renders
6. WHEN batch verification completes, THE VoicePrint_System SHALL release temporary resources

### Requirement 12: Configuration Format Parsing

**User Story:** As a developer, I want to parse configuration files, so that I can load application settings and model parameters.

#### Acceptance Criteria

1. WHEN a valid JSON configuration file is provided, THE Config_Parser SHALL parse it into a Configuration object
2. WHEN an invalid JSON configuration file is provided, THE Config_Parser SHALL return a descriptive error
3. THE Config_Formatter SHALL format Configuration objects back into valid JSON files
4. FOR ALL valid Configuration objects, parsing then formatting then parsing SHALL produce an equivalent object (round-trip property)
5. THE Configuration object SHALL include model_path, threshold, sample_rate, and storage_path fields

### Requirement 13: End-to-End System Validation

**User Story:** As a quality assurance engineer, I want comprehensive system validation, so that I can verify all components work together correctly.

#### Acceptance Criteria

1. THE VoicePrint_System SHALL successfully complete enrollment with 50 or more WAV files
2. THE VoicePrint_System SHALL successfully verify identity using live microphone input
3. THE VoicePrint_System SHALL successfully process batch verification requests
4. THE VoicePrint_System SHALL handle all error scenarios defined in the error handling matrix
5. THE VoicePrint_System SHALL operate without any cloud or external network dependencies
6. WHEN stereo audio is enrolled and mono audio is verified, THE VoicePrint_System SHALL produce consistent similarity scores (format invariance)
7. WHEN audio is resampled from different source rates, THE VoicePrint_System SHALL produce comparable embeddings (rate invariance)
