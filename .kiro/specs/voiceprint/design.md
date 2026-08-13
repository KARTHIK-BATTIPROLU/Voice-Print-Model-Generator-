# Design Document: VoicePrint Voice Biometric Platform

## Overview

VoicePrint is a locally-hosted voice biometric platform that enables speaker enrollment and verification using deep learning embeddings. The system extracts voice characteristics using SpeechBrain's pretrained ECAPA-TDNN model, creates unique voiceprints through embedding averaging, and performs speaker verification via cosine similarity scoring. All processing occurs locally without cloud dependencies.

### System Architecture Philosophy

The design follows a clean separation between:
- **Backend (Python/FastAPI)**: Model inference, audio processing, persistence, RESTful API
- **Frontend (React/Vite)**: User interface, real-time visualization, local audio processing
- **Shared Protocol**: JSON-based REST API with WebSocket for progress streaming

### Key Design Principles

1. **Local-First**: Zero cloud dependencies, all ML inference and data storage happens locally
2. **Pretrained Model**: Use SpeechBrain's ECAPA-TDNN without fine-tuning to ensure reproducibility
3. **Singleton Pattern**: Single model instance loaded at startup for memory efficiency
4. **File-Based Storage**: Simple, transparent persistence using numpy arrays and JSON
5. **Progressive Enhancement**: Basic REST API for all operations, WebSocket for enhanced progress tracking
6. **Responsive Design**: Dark theme with custom-built components, no external UI libraries

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────┐ │
│  │Dashboard │  │  Enroll  │  │Verify Live│  │Verify Batch│ │
│  └──────────┘  └──────────┘  └───────────┘  └───────────┘ │
│        │              │              │              │        │
│        └──────────────┴──────────────┴──────────────┘        │
│                         │                                    │
│                    API Client (api.js)                       │
│                         │                                    │
└─────────────────────────┼────────────────────────────────────┘
                          │ HTTP/WS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    API Routes                           │ │
│  │  /enroll  /verify  /profiles  /health  /ws/progress   │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│  ┌──────────────┬────────────────┬──────────────────────┐  │
│  │Model Loader  │Audio Processor │  Embedding Engine    │  │
│  │(Singleton)   │(WAV Utils)     │  (ECAPA-TDNN)        │  │
│  └──────────────┴────────────────┴──────────────────────┘  │
│                          │                                   │
│                   Profile Store                              │
│             (File System: profiles/{name}/)                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  File System Storage   │
              │  profiles/             │
              │    └─ {name}/          │
              │       ├─ voiceprint.npy│
              │       └─ meta.json     │
              └────────────────────────┘
```

### Component Interaction Flow

**Enrollment Flow:**
```
User Upload → Frontend → API Client → /enroll endpoint
                                           ↓
                                    Audio Processor
                                    (validate, resample)
                                           ↓
                                    Embedding Engine
                                    (extract, normalize, average)
                                           ↓
                                    Profile Store
                                    (persist voiceprint + metadata)
                                           ↓
                                    WebSocket Progress Updates
                                    (for >30 files)
```

**Verification Flow:**
```
Audio Input → Frontend → API Client → /verify endpoint
                                           ↓
                                    Audio Processor
                                    (validate, resample)
                                           ↓
                                    Embedding Engine
                                    (extract, normalize)
                                           ↓
                                    Profile Store
                                    (load voiceprint)
                                           ↓
                                    Cosine Similarity
                                    (compute score)
                                           ↓
                                    Return score + pass/fail
```

### Technology Stack

**Backend:**
- **Framework**: FastAPI (async, automatic OpenAPI docs)
- **ML Framework**: PyTorch (required by SpeechBrain)
- **Model**: SpeechBrain ECAPA-TDNN (`speechbrain/spkrec-ecapa-voxceleb`)
- **Audio Processing**: torchaudio, librosa
- **Numerical Computing**: numpy (embedding storage and operations)
- **File Format Conversion**: ffmpeg-python (WebM to WAV)
- **WebSocket**: FastAPI's built-in WebSocket support

**Frontend:**
- **Framework**: React 18
- **Build Tool**: Vite (fast dev server, optimized builds)
- **Audio API**: Web Audio API (microphone capture, waveform visualization)
- **Styling**: Custom CSS (no UI libraries, hand-built components)
- **HTTP Client**: fetch API
- **State Management**: React hooks (useState, useEffect, useContext)

**Storage:**
- **Embeddings**: numpy `.npy` files (efficient binary format)
- **Metadata**: JSON files (human-readable, easy debugging)
- **File Structure**: `profiles/{profile_name}/[voiceprint.npy, meta.json]`

## Components and Interfaces

### Backend Components

#### 1. Model Loader (`model.py`)

**Responsibility**: Manage singleton ECAPA-TDNN model instance with thread-safe access.

**Interface:**
```python
class ModelLoader:
    @staticmethod
    def get_instance() -> EncoderClassifier:
        """Returns singleton model instance, loads if not already loaded"""
        
    @staticmethod
    def is_loaded() -> bool:
        """Check if model is loaded and ready"""
```

**Implementation Details:**
- Singleton pattern using class-level variable + lock
- Thread-safe with `threading.Lock()`
- Lazy loading: model loaded on first `get_instance()` call
- Model source: `speechbrain/spkrec-ecapa-voxceleb`
- No fine-tuning or model modification

**Dependencies:**
- `speechbrain.pretrained.EncoderClassifier`

---

#### 2. Audio Processor (`audio_utils.py`)

**Responsibility**: Validate, resample, and segment audio files for embedding extraction.

**Interface:**
```python
def validate_wav(file_path: str) -> dict:
    """Validate WAV file format and return metadata
    
    Returns:
        {
            "valid": bool,
            "sample_rate": int,
            "channels": int,
            "duration": float,
            "error": str | None
        }
    """

def resample_audio(waveform: torch.Tensor, orig_sr: int, target_sr: int = 16000) -> torch.Tensor:
    """Resample audio to target sample rate"""

def convert_to_mono(waveform: torch.Tensor) -> torch.Tensor:
    """Convert stereo/multi-channel audio to mono"""

def estimate_snr(waveform: torch.Tensor, sample_rate: int) -> float:
    """Estimate Signal-to-Noise Ratio in dB"""

def segment_audio(waveform: torch.Tensor, sample_rate: int, segment_length: float = 10.0) -> list[torch.Tensor]:
    """Segment long audio into chunks for processing"""

def load_and_preprocess(file_path: str) -> tuple[torch.Tensor, dict]:
    """Load WAV file and apply all preprocessing steps
    
    Returns:
        (preprocessed_waveform, metadata)
    """
```

**Validation Rules:**
- Sample rate: 8kHz - 48kHz
- Minimum duration: 1.5 seconds
- Minimum SNR: 5dB
- Format: WAV (RIFF header validation)
- Maximum file size: 50MB

**Preprocessing Pipeline:**
1. Load WAV file using torchaudio
2. Validate format and extract metadata
3. Convert to mono if stereo/multi-channel
4. Resample to 16kHz (ECAPA-TDNN target rate)
5. Estimate SNR and filter low-quality samples
6. Normalize amplitude to [-1, 1] range

---

#### 3. Embedding Engine (`embedding.py`)

**Responsibility**: Extract voice embeddings, normalize, average, and compute similarity.

**Interface:**
```python
def extract_embedding(waveform: torch.Tensor, sample_rate: int) -> np.ndarray:
    """Extract ECAPA-TDNN embedding from audio waveform
    
    Returns:
        192-dimensional embedding vector
    """

def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    """Apply L2 normalization to embedding"""

def average_embeddings(embeddings: list[np.ndarray]) -> np.ndarray:
    """Compute mean embedding from list of normalized embeddings"""

def compute_cosine_similarity(embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
    """Compute cosine similarity between two embeddings
    
    Returns:
        Similarity score in range [-1, 1]
    """

def detect_outliers(embeddings: list[np.ndarray], threshold: float = 2.5) -> list[int]:
    """Detect outlier embeddings using z-score method
    
    Returns:
        List of indices for outlier embeddings
    """

def compute_intra_class_stats(embeddings: list[np.ndarray]) -> dict:
    """Compute statistics for enrollment sample cohesion
    
    Returns:
        {
            "mean_similarity": float,
            "std_similarity": float,
            "min_similarity": float,
            "max_similarity": float
        }
    """
```

**Embedding Details:**
- Model: ECAPA-TDNN pretrained on VoxCeleb
- Embedding dimension: 192
- Normalization: L2 (unit vector)
- Averaging: Element-wise mean of normalized embeddings
- Similarity metric: Cosine similarity (dot product of normalized vectors)

**Outlier Detection:**
- Method: Z-score on pairwise similarities
- Threshold: 2.5 standard deviations
- Purpose: Flag low-quality samples during enrollment

---

#### 4. Profile Store (`profile_store.py`)

**Responsibility**: Persist and retrieve voiceprint profiles from file system.

**Interface:**
```python
class ProfileStore:
    def __init__(self, base_path: str = "profiles"):
        """Initialize profile store with base directory"""
    
    def create_profile(self, name: str, voiceprint: np.ndarray, metadata: dict) -> bool:
        """Create new profile with voiceprint and metadata
        
        Creates:
            profiles/{name}/voiceprint.npy
            profiles/{name}/meta.json
        """
    
    def get_profile(self, name: str) -> dict | None:
        """Retrieve profile by name
        
        Returns:
            {
                "name": str,
                "voiceprint": np.ndarray,
                "metadata": dict
            }
        """
    
    def list_profiles(self) -> list[dict]:
        """List all profiles with metadata"""
    
    def delete_profile(self, name: str) -> bool:
        """Delete profile and all associated files"""
    
    def update_threshold(self, name: str, threshold: float) -> bool:
        """Update profile-specific threshold in metadata"""
    
    def profile_exists(self, name: str) -> bool:
        """Check if profile exists"""
```

**File Structure:**
```
profiles/
├── alice/
│   ├── voiceprint.npy    # 192-dim numpy array
│   └── meta.json         # {"created": ISO8601, "sample_count": int, "threshold": float, ...}
├── bob/
│   ├── voiceprint.npy
│   └── meta.json
└── ...
```

**Metadata Schema:**
```json
{
    "created": "2024-01-15T10:30:00Z",
    "sample_count": 25,
    "threshold": 0.7,
    "intra_class_stats": {
        "mean_similarity": 0.85,
        "std_similarity": 0.05,
        "min_similarity": 0.72,
        "max_similarity": 0.95
    },
    "outliers_detected": [3, 17],
    "last_verified": "2024-01-16T14:20:00Z"
}
```

**Atomic Write Strategy:**
- Write to temporary file first (`.tmp` suffix)
- Perform atomic rename after successful write
- Prevents corruption if write is interrupted

---

#### 5. API Routes (`main.py`)

**Responsibility**: Expose REST API endpoints and WebSocket for frontend communication.

**Endpoints:**

**POST /api/enroll**
```
Request:
  - multipart/form-data
  - profile_name: string
  - files: list[File] (10-500 WAV files)

Response:
  {
    "success": bool,
    "profile_name": str,
    "voiceprint_created": bool,
    "samples_processed": int,
    "samples_rejected": int,
    "outliers_detected": list[int],
    "intra_class_stats": dict,
    "error": str | null
  }
```

**POST /api/verify**
```
Request:
  {
    "profile_name": str,
    "audio_file": File (WAV)
  }

Response:
  {
    "success": bool,
    "profile_name": str,
    "similarity_score": float,
    "threshold": float,
    "verified": bool,
    "error": str | null
  }
```

**POST /api/verify/batch**
```
Request:
  - multipart/form-data
  - profile_name: string
  - files: list[File] (WAV files)

Response:
  {
    "success": bool,
    "profile_name": str,
    "results": [
      {
        "filename": str,
        "similarity_score": float,
        "verified": bool
      },
      ...
    ],
    "error": str | null
  }
```

**GET /api/profiles**
```
Response:
  {
    "profiles": [
      {
        "name": str,
        "created": str (ISO8601),
        "sample_count": int,
        "threshold": float,
        "intra_class_stats": dict
      },
      ...
    ]
  }
```

**GET /api/profiles/{name}**
```
Response:
  {
    "name": str,
    "metadata": dict,
    "exists": bool
  }
```

**DELETE /api/profiles/{name}**
```
Response:
  {
    "success": bool,
    "deleted": bool,
    "error": str | null
  }
```

**PATCH /api/profiles/{name}/threshold**
```
Request:
  {
    "threshold": float (0.0 - 1.0)
  }

Response:
  {
    "success": bool,
    "updated": bool,
    "error": str | null
  }
```

**GET /api/health**
```
Response:
  {
    "status": "healthy" | "unhealthy",
    "model_loaded": bool,
    "profile_count": int,
    "uptime": float (seconds)
  }
```

**WebSocket /ws/progress/{session_id}**
```
Progress Messages:
  {
    "type": "progress",
    "current": int,
    "total": int,
    "percentage": float,
    "message": str
  }

Completion Message:
  {
    "type": "complete",
    "success": bool,
    "result": dict
  }
```

**CORS Configuration:**
- Allow origins: `http://localhost:5173` (Vite dev server)
- Allow methods: GET, POST, DELETE, PATCH
- Allow headers: Content-Type, Authorization

---

### Frontend Components

#### 1. API Client (`api.js`)

**Responsibility**: Centralized API communication layer.

**Interface:**
```javascript
// Profile Management
export async function getProfiles()
export async function getProfile(name)
export async function deleteProfile(name)
export async function updateProfileThreshold(name, threshold)

// Enrollment
export async function enrollProfile(name, files, onProgress)

// Verification
export async function verifyLive(profileName, audioBlob)
export async function verifyBatch(profileName, files)

// Health
export async function getHealth()

// WebSocket
export function connectProgressWebSocket(sessionId, onProgress, onComplete)
```

**Error Handling:**
- Automatic retry on network failures (max 3 attempts)
- Timeout handling (30s for enrollment, 10s for verification)
- Descriptive error messages extracted from API responses

---

#### 2. Dashboard Page (`Dashboard.jsx`)

**Responsibility**: Display profile grid with management actions.

**Features:**
- Grid layout of profile cards (responsive: 1/2/3 columns)
- Each card shows: name, sample count, creation date, intra-class stats
- Action buttons: "Verify Live", "Verify Batch", "Delete"
- Health indicator in header
- Empty state message when no profiles exist

**State:**
```javascript
{
  profiles: Profile[],
  loading: boolean,
  error: string | null,
  health: HealthStatus
}
```

---

#### 3. Enroll Page (`Enroll.jsx`)

**Responsibility**: Handle profile enrollment with progress tracking.

**Features:**
- Profile name input (alphanumeric + allowed special chars)
- Folder upload button (accept: `.wav`)
- File count display (must be 10-500)
- Progress ring during enrollment
- Enrollment summary on completion:
  - Samples processed/rejected
  - Outliers detected
  - Intra-class statistics
  - Mean similarity score

**State:**
```javascript
{
  profileName: string,
  files: File[],
  uploading: boolean,
  progress: number,
  result: EnrollmentResult | null,
  error: string | null
}
```

---

#### 4. Verify Live Page (`VerifyLive.jsx`)

**Responsibility**: Real-time microphone verification with waveform visualization.

**Features:**
- Profile selector dropdown
- Animated waveform ring (Web Audio API)
- Record button with visual feedback
- Recording timer
- Score gauge showing similarity score
- Pass/fail indicator with color coding
- Option to save recording locally

**State:**
```javascript
{
  selectedProfile: string | null,
  recording: boolean,
  audioBlob: Blob | null,
  analyzing: boolean,
  result: VerificationResult | null,
  error: string | null
}
```

**Waveform Ring Component:**
- Uses `AnalyserNode` for real-time frequency data
- SVG-based circular visualization
- Amplitude mapped to ring radius
- Color gradient based on volume level

---

#### 5. Verify Batch Page (`VerifyBatch.jsx`)

**Responsibility**: Batch verification with threshold adjustment and CSV export.

**Features:**
- Profile selector dropdown
- Multi-file upload
- Threshold slider (0.0 - 1.0) with live updates
- Sortable table:
  - Columns: Filename, Score, Status
  - Click header to sort
  - Color-coded pass/fail rows
- CSV export button
- Summary statistics (pass rate, mean score, std dev)

**State:**
```javascript
{
  selectedProfile: string | null,
  files: File[],
  threshold: number,
  results: VerificationResult[],
  sortBy: 'filename' | 'score' | 'status',
  sortOrder: 'asc' | 'desc',
  loading: boolean,
  error: string | null
}
```

**CSV Export Format:**
```
Filename,Score,Threshold,Verified,Timestamp
sample1.wav,0.82,0.7,true,2024-01-15T10:30:00Z
sample2.wav,0.45,0.7,false,2024-01-15T10:30:01Z
...
```

---

#### 6. Shared Components

**ProfileCard Component:**
- Display: profile name, sample count, creation date
- Visual: card with hover effect
- Actions: buttons for verify/delete

**ProgressRing Component:**
- SVG circular progress indicator
- Props: `percentage`, `size`, `strokeWidth`, `color`

**ScoreGauge Component:**
- SVG arc gauge (180° semicircle)
- Score mapped to arc fill
- Color gradient: red (0.0) → yellow (0.5) → green (1.0)
- Threshold indicator line

**WaveformRing Component:**
- Real-time audio visualization
- Web Audio API integration
- Circular waveform display

---

### Design System

**Color Palette:**
```css
--background: #0A0A0F;          /* Deep space black */
--surface: #16161F;              /* Card background */
--surface-hover: #1F1F2E;        /* Hover state */
--accent: #6C63FF;               /* Electric violet */
--accent-hover: #5A52D5;         /* Darker violet */
--text-primary: #E8E8F0;         /* Almost white */
--text-secondary: #9999AA;       /* Muted gray */
--success: #00D9A3;              /* Teal green */
--error: #FF6B6B;                /* Coral red */
--warning: #FFB84D;              /* Amber yellow */
--border: #2A2A3A;               /* Subtle border */
```

**Typography:**
```css
--font-display: 'Space Grotesk', sans-serif;  /* Headers */
--font-body: 'Inter', sans-serif;              /* Body text */
--font-mono: 'JetBrains Mono', monospace;      /* Technical info */

--text-xl: 2rem;     /* Page titles */
--text-lg: 1.5rem;   /* Section headers */
--text-md: 1rem;     /* Body text */
--text-sm: 0.875rem; /* Labels */
--text-xs: 0.75rem;  /* Captions */
```

**Spacing Scale:**
```css
--space-xs: 0.25rem;   /* 4px */
--space-sm: 0.5rem;    /* 8px */
--space-md: 1rem;      /* 16px */
--space-lg: 1.5rem;    /* 24px */
--space-xl: 2rem;      /* 32px */
--space-2xl: 3rem;     /* 48px */
```

**Component Styling:**
- Border radius: 8px (cards), 4px (buttons)
- Shadows: Subtle elevation with glow effect
- Transitions: 200ms ease-in-out
- Focus states: 2px accent color outline

## Data Models

### Embedding Vector

**Format:** numpy array (float32)
**Dimensions:** 192
**Normalization:** L2 (unit vector)
**Storage:** `.npy` binary format

```python
voiceprint: np.ndarray  # shape: (192,), dtype: float32
```

**Properties:**
- L2 norm = 1.0 (unit vector)
- Represents speaker-specific voice characteristics
- Derived from ECAPA-TDNN final layer activations

---

### Profile Metadata

**Format:** JSON
**Storage:** `meta.json` per profile

```typescript
interface ProfileMetadata {
  created: string;              // ISO8601 timestamp
  sample_count: number;         // Number of enrollment samples
  threshold: number;            // Verification threshold (0.0 - 1.0)
  intra_class_stats: {
    mean_similarity: number;    // Mean pairwise similarity
    std_similarity: number;     // Standard deviation
    min_similarity: number;     // Minimum pairwise similarity
    max_similarity: number;     // Maximum pairwise similarity
  };
  outliers_detected: number[];  // Indices of outlier samples
  last_verified: string | null; // ISO8601 timestamp of last verification
  version: string;              // Schema version (e.g., "1.0")
}
```

---

### Audio File Metadata

**Extracted during preprocessing:**

```typescript
interface AudioMetadata {
  sample_rate: number;          // Original sample rate (Hz)
  channels: number;             // 1 (mono) or 2 (stereo)
  duration: number;             // Duration in seconds
  snr_db: number;               // Signal-to-Noise Ratio (dB)
  format: string;               // "wav"
  bit_depth: number;            // 16 or 24
  preprocessed: boolean;        // Whether audio was resampled/converted
}
```

---

### Verification Result

**API response model:**

```typescript
interface VerificationResult {
  success: boolean;
  profile_name: string;
  similarity_score: number;     // Cosine similarity (-1 to 1)
  threshold: number;            // Applied threshold
  verified: boolean;            // score >= threshold
  metadata: {
    audio_duration: number;
    snr_db: number;
    processing_time_ms: number;
  };
  error: string | null;
}
```

---

### Enrollment Result

**API response model:**

```typescript
interface EnrollmentResult {
  success: boolean;
  profile_name: string;
  voiceprint_created: boolean;
  samples_processed: number;    // Successfully processed samples
  samples_rejected: number;     // Rejected (SNR/duration)
  outliers_detected: number[];  // Outlier sample indices
  intra_class_stats: {
    mean_similarity: number;
    std_similarity: number;
    min_similarity: number;
    max_similarity: number;
  };
  metadata: {
    total_duration: number;     // Total audio duration (seconds)
    mean_snr_db: number;        // Mean SNR across samples
    processing_time_ms: number;
  };
  error: string | null;
}
```

---

### Configuration Model

**Application configuration:**

```typescript
interface AppConfig {
  model_path: string;           // SpeechBrain model identifier
  storage_path: string;         // Base path for profiles
  default_threshold: number;    // Default verification threshold
  target_sample_rate: number;   // Target sample rate (16000 Hz)
  min_snr_db: number;           // Minimum SNR threshold (5 dB)
  min_duration_sec: number;     // Minimum audio duration (1.5 sec)
  max_file_size_mb: number;     // Maximum file size (50 MB)
  enrollment: {
    min_samples: number;        // Minimum samples for enrollment (10)
    max_samples: number;        // Maximum samples for enrollment (500)
    outlier_threshold: number;  // Z-score threshold for outliers (2.5)
  };
  server: {
    host: string;               // "0.0.0.0"
    port: number;               // 8000
    cors_origins: string[];     // ["http://localhost:5173"]
  };
}
```

---

### Batch Verification Result

**CSV export and API response:**

```typescript
interface BatchVerificationResult {
  success: boolean;
  profile_name: string;
  results: Array<{
    filename: string;
    similarity_score: number;
    verified: boolean;
    metadata: {
      duration: number;
      snr_db: number;
    };
  }>;
  summary: {
    total_files: number;
    verified_count: number;
    failed_count: number;
    pass_rate: number;          // Percentage
    mean_score: number;
    std_score: number;
  };
  threshold: number;
  error: string | null;
}
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following properties for testing. Several criteria reference the same underlying operations (e.g., embedding extraction, L2 normalization, similarity computation) which appear in multiple requirements. To avoid redundancy, I consolidated these into single comprehensive properties that validate the core behavior across all contexts.

**Redundancies eliminated:**
- Requirements 1.6, 2.5: Both test embedding extraction → consolidated into Property 1
- Requirements 1.7, 2.6: Both test L2 normalization → consolidated into Property 2
- Requirements 2.7, 3.2, 9.3: All test cosine similarity → consolidated into Property 7
- Requirements 1.3, 2.4: Both test resampling to 16kHz mono → consolidated into Property 3
- Requirements 6.6, 9.5: Both test threshold configuration → consolidated into Property 17

### Property 1: Embedding Extraction Produces Valid Vectors

*For any* valid audio waveform with duration ≥1.5 seconds and sample rate of 16kHz, the embedding extraction SHALL produce a 192-dimensional numpy array.

**Validates: Requirements 1.6, 2.5**

### Property 2: L2 Normalization Produces Unit Vectors

*For any* embedding vector extracted from audio, applying L2 normalization SHALL produce a vector with L2 norm equal to 1.0 (±1e-6 tolerance).

**Validates: Requirements 1.7, 2.6**

### Property 3: Audio Resampling Preserves Validity

*For any* valid WAV file with sample rate between 8kHz and 48kHz, resampling to 16kHz mono SHALL produce valid audio with sample rate of 16000 Hz, 1 channel, and amplitude values in range [-1.0, 1.0] with no NaN or infinite values.

**Validates: Requirements 1.3, 2.4, 5.7**

### Property 4: Enrollment File Count Validation

*For any* enrollment request with N audio files, the system SHALL accept the request if and only if 10 ≤ N ≤ 500.

**Validates: Requirements 1.1**

### Property 5: WAV Format Validation

*For any* file submitted for processing, the Audio_Processor SHALL correctly identify whether it is a valid WAV file by checking RIFF header compliance and return appropriate validation status.

**Validates: Requirements 1.2, 5.3**

### Property 6: Voiceprint Averaging Correctness

*For any* non-empty collection of L2-normalized embeddings, the averaged voiceprint SHALL equal the element-wise mean of all input embeddings.

**Validates: Requirements 1.8**

### Property 7: Cosine Similarity Computation

*For any* pair of L2-normalized embedding vectors A and B, the computed cosine similarity SHALL equal the dot product of A and B (since both are unit vectors).

**Validates: Requirements 2.7, 3.2, 9.3**

### Property 8: Cosine Similarity Identity Property

*For any* valid voiceprint embedding E, computing cosine similarity with itself SHALL produce a score of 1.0 (±1e-6 tolerance).

**Validates: Requirements 9.6**

### Property 9: Cosine Similarity Commutativity

*For any* pair of embedding vectors A and B, cosine_similarity(A, B) SHALL equal cosine_similarity(B, A).

**Validates: Requirements 9.7**

### Property 10: Threshold Comparison Logic

*For any* similarity score S and threshold T, the verification result SHALL be pass (True) if and only if S ≥ T.

**Validates: Requirements 2.8**

### Property 11: Voiceprint Persistence Round-Trip

*For any* valid voiceprint embedding array, saving to `.npy` format then loading SHALL produce a numpy array equal to the original (element-wise comparison with tolerance 1e-7).

**Validates: Requirements 1.11**

### Property 12: Metadata JSON Round-Trip

*For any* valid ProfileMetadata object, serializing to JSON then deserializing SHALL produce an equivalent object with all fields preserved.

**Validates: Requirements 1.12**

### Property 13: Batch Results CSV Round-Trip

*For any* batch verification results, exporting to CSV then parsing SHALL produce equivalent data structure with all filenames, scores, and verification status preserved.

**Validates: Requirements 3.6, 3.7**

### Property 14: Configuration Round-Trip

*For any* valid Configuration object, formatting to JSON then parsing SHALL produce an equivalent configuration with all fields (model_path, threshold, sample_rate, storage_path) preserved.

**Validates: Requirements 12.4**

### Property 15: Intra-Class Statistics Computation

*For any* collection of embeddings E = {e1, e2, ..., en}, the computed intra-class statistics SHALL correctly reflect:
- mean_similarity = mean of all pairwise cosine similarities
- std_similarity = standard deviation of all pairwise cosine similarities
- min_similarity = minimum pairwise cosine similarity
- max_similarity = maximum pairwise cosine similarity

**Validates: Requirements 1.9**

### Property 16: Model Singleton Pattern

*For any* sequence of calls to ModelLoader.get_instance(), all calls SHALL return the same object instance (verified by identity comparison with `is`).

**Validates: Requirements 4.1, 4.5**

### Property 17: Profile Threshold Configuration Round-Trip

*For any* valid threshold value T in range [0.0, 1.0], updating a profile's threshold to T then retrieving the profile SHALL return threshold equal to T.

**Validates: Requirements 6.6, 9.5**

### Property 18: Sample Rate Validation

*For any* WAV file with sample rate R Hz, the Audio_Processor SHALL accept the file if and only if 8000 ≤ R ≤ 48000.

**Validates: Requirements 5.1**

### Property 19: Stereo to Mono Conversion

*For any* stereo audio waveform (2 channels), conversion to mono SHALL produce a waveform with exactly 1 channel and duration equal to the original (±0.01 seconds).

**Validates: Requirements 5.2**

### Property 20: Audio Segmentation Correctness

*For any* audio waveform of duration D seconds and segment length L seconds, segmentation SHALL produce ⌈D/L⌉ segments where all segments except possibly the last have duration L seconds (±0.01s).

**Validates: Requirements 5.6**

### Property 21: Profile Deletion Cleanup

*For any* existing profile with name N, after deletion the profile directory `profiles/N/` SHALL not exist and SHALL contain no files.

**Validates: Requirements 6.5, 6.9**

### Property 22: Client-Side Threshold Update

*For any* batch verification results with original threshold T1 and new threshold T2, updating the threshold client-side SHALL recalculate pass/fail status for all results using T2 without changing similarity scores.

**Validates: Requirements 3.5**

### Property 23: Format Invariance for Embeddings

*For any* audio sample of a speaker, embeddings extracted from stereo and mono versions of the same audio SHALL have cosine similarity ≥ 0.95 (accounting for minor format conversion differences).

**Validates: Requirements 13.6**

### Property 24: Sample Rate Invariance for Embeddings

*For any* audio sample at different source sample rates within valid range (8-48kHz), after resampling all to 16kHz, the extracted embeddings SHALL have pairwise cosine similarities ≥ 0.95.

**Validates: Requirements 13.7**

### Property 25: Thread-Safe Concurrent Model Access

*For any* collection of N concurrent embedding extraction requests, all requests SHALL complete successfully without errors, and all SHALL receive embeddings from the same model instance.

**Validates: Requirements 4.3, 4.5**

### Property 26: Batch Verification Processes All Files

*For any* collection of audio files submitted for batch verification, the results SHALL contain exactly one entry per input file with corresponding filename, score, and verification status.

**Validates: Requirements 3.1**

## Error Handling

### Error Classification Matrix

The system handles errors across four categories:

| Category | Examples | Response Strategy | HTTP Status |
|----------|----------|------------------|-------------|
| **Validation Errors** | Invalid format, insufficient samples, file too large | Return descriptive error message | 400 Bad Request |
| **Resource Errors** | Profile not found, file access denied | Return specific resource error | 404 Not Found |
| **Processing Errors** | Model inference failure, audio corruption | Log full error, return generic message | 500 Internal Server Error |
| **System Errors** | Model loading failure, disk full | Log critical error, return system unavailable | 503 Service Unavailable |

### Specific Error Scenarios

**1. Invalid Audio Format**
- Trigger: Non-WAV file or corrupted WAV header
- Response: `{"error": "Invalid audio format. Only WAV files are supported."}`
- Action: Reject file, continue with remaining files in batch

**2. Insufficient Enrollment Samples**
- Trigger: Fewer than 10 audio files provided
- Response: `{"error": "Minimum 10 samples required for enrollment. Provided: {count}"}`
- Action: Reject enrollment request entirely

**3. Audio Duration Too Short**
- Trigger: Audio sample shorter than 1.5 seconds
- Response: `{"error": "Audio must be at least 1.5 seconds. Duration: {duration}s"}`
- Action: Skip sample, continue with remaining samples

**4. Profile Not Found**
- Trigger: Verification requested for non-existent profile
- Response: `{"error": "Profile '{name}' not found."}`
- Action: Return 404, suggest listing available profiles

**5. File Size Exceeds Limit**
- Trigger: File larger than 50MB
- Response: `{"error": "File size exceeds maximum of 50MB. Size: {size}MB"}`
- Action: Reject file, continue with remaining files

**6. Model Initialization Failed**
- Trigger: SpeechBrain model fails to load at startup
- Response: `{"error": "Model initialization failed. Please restart the service."}`
- Action: Return 503, log detailed traceback, prevent API from accepting requests

**7. Profile Name Invalid**
- Trigger: Profile name contains invalid characters
- Response: `{"error": "Profile name must contain only alphanumeric characters, hyphens, and underscores."}`
- Action: Reject request with 400

**8. Low SNR Sample**
- Trigger: Audio SNR below 5dB threshold
- Response: Sample filtered silently, included in `samples_rejected` count
- Action: Skip sample, log SNR value, continue enrollment

**9. Outlier Sample Detected**
- Trigger: Z-score > 2.5 for sample similarity
- Response: Sample included but flagged in `outliers_detected` list
- Action: Include sample in enrollment, flag index in metadata

**10. Concurrent Model Access Failure**
- Trigger: Thread synchronization error
- Response: `{"error": "Internal processing error. Please try again."}`
- Action: Return 500, log threading error, ensure locks are released

### Input Validation and Sanitization

**Profile Names:**
- Allowed characters: `a-z`, `A-Z`, `0-9`, `-`, `_`
- Maximum length: 64 characters
- Sanitization: Strip whitespace, reject if pattern doesn't match `^[a-zA-Z0-9_-]{1,64}$`

**File Uploads:**
- Size limit: 50MB per file
- Type validation: Check RIFF header, not just extension
- Batch limit: Maximum 500 files per enrollment

**Threshold Values:**
- Range: [0.0, 1.0]
- Validation: Reject if outside range or not a number

**Audio Processing:**
- NaN/Inf detection: Reject if audio contains non-finite values after processing
- Amplitude clipping: Warn if >1% of samples exceed [-1, 1] range

### Security Considerations

**Path Traversal Prevention:**
- Profile names sanitized to prevent `../` attacks
- All file operations use `os.path.join()` with validated base path

**Injection Attack Prevention:**
- No shell commands with user input
- JSON serialization uses standard library (no eval)
- Profile names validated against strict regex pattern

**Resource Exhaustion Prevention:**
- Maximum file size enforcement (50MB)
- Maximum enrollment batch size (500 files)
- Request timeout: 300 seconds for enrollment, 30 seconds for verification

**Error Information Disclosure:**
- Generic errors for unexpected failures (hide stack traces from clients)
- Detailed errors only for validation issues
- System errors logged server-side only

## Testing Strategy

### Testing Philosophy

VoicePrint uses a dual testing approach:

1. **Property-Based Testing (PBT)**: Validates universal properties across the core audio processing, embedding, and similarity computation logic
2. **Example-Based Testing**: Validates specific scenarios, UI behavior, integration points, and error handling

### Property-Based Testing Strategy

**Library Selection:**
- **Backend (Python)**: Hypothesis for property-based testing
- **Frontend (JavaScript)**: fast-check for property-based testing

**Test Configuration:**
- Minimum iterations: 100 per property test
- Random seed: Configurable for reproducibility
- Shrinking: Enabled to find minimal failing examples

**Property Test Tags:**
Each property test MUST include a comment tag in the following format:
```python
# Feature: voiceprint, Property 1: Embedding Extraction Produces Valid Vectors
```

**Property Test Organization:**
```
backend/
  tests/
    properties/
      test_embedding_properties.py      # Properties 1, 2, 7, 8, 9, 23, 24
      test_audio_processing_properties.py # Properties 3, 5, 18, 19, 20
      test_persistence_properties.py     # Properties 11, 12, 13, 14
      test_profile_properties.py         # Properties 17, 21
      test_model_properties.py           # Properties 16, 25
      test_verification_properties.py    # Properties 10, 22, 26
      test_enrollment_properties.py      # Properties 4, 6, 15
```

**Generator Strategies:**

*Audio Generators:*
- Sample rates: Uniformly from [8000, 48000] Hz
- Durations: Uniformly from [0.5, 30.0] seconds (includes invalid <1.5s)
- Channels: Choice of 1 (mono) or 2 (stereo)
- SNR: Uniformly from [0, 30] dB (includes invalid <5dB)
- Waveform types: Sine waves, noise, silence, combined (for controlled testing)

*Embedding Generators:*
- Dimension: Fixed at 192
- Values: Normal distribution N(0, 0.1) then L2 normalized
- Batch sizes: Integers from [1, 100]

*Profile Name Generators:*
- Valid names: Regex `^[a-zA-Z0-9_-]{1,64}$`
- Invalid names: Include spaces, special chars, empty strings, >64 chars

*Configuration Generators:*
- Threshold: Floats from [0.0, 1.0]
- Sample rate: Choice of common rates [8000, 16000, 22050, 44100, 48000]
- File paths: Valid path strings

### Unit Testing Strategy

**Test Organization:**
```
backend/
  tests/
    unit/
      test_model_loader.py
      test_audio_utils.py
      test_embedding.py
      test_profile_store.py
      test_api_routes.py

frontend/
  src/
    components/
      __tests__/
        Waveform.test.jsx
        ScoreGauge.test.jsx
        ProfileCard.test.jsx
    pages/
      __tests__/
        Dashboard.test.jsx
        Enroll.test.jsx
        VerifyLive.test.jsx
        VerifyBatch.test.jsx
```

**Unit Test Coverage:**
- Model loading and singleton behavior (examples)
- Audio validation error messages (specific error cases)
- Profile CRUD operations (create, read, update, delete examples)
- API endpoint response formats (example requests/responses)
- UI component rendering (snapshot tests)
- Error handling for each error scenario in error matrix

### Integration Testing Strategy

**Integration Test Scenarios:**

1. **End-to-End Enrollment:**
   - Upload 50 WAV files
   - Verify profile created with correct metadata
   - Verify voiceprint.npy and meta.json exist
   - Verify statistics computed

2. **End-to-End Verification:**
   - Enroll speaker with 20 samples
   - Verify with same speaker sample (expect pass)
   - Verify with different speaker sample (expect fail)

3. **WebSocket Progress:**
   - Enroll with 35 files
   - Connect to WebSocket
   - Verify progress messages received
   - Verify completion message

4. **Batch Verification Workflow:**
   - Enroll speaker
   - Upload 10 test files
   - Verify all processed
   - Export CSV
   - Verify CSV format

5. **Model Behavior:**
   - Test same-speaker similarity >0.8
   - Test different-speaker similarity <0.5
   - Test with real audio samples from VoxCeleb test set

6. **Frontend-Backend Integration:**
   - Test CORS headers
   - Test JSON serialization
   - Test error propagation
   - Test WebM to WAV conversion

**Integration Test Environment:**
- Dedicated test profiles directory
- Sample audio files from VoxCeleb test set
- Mock WebSocket for frontend tests
- In-memory profile store for fast tests

### Performance Testing

**Benchmarks:**
- Model loading time: <30 seconds at startup
- Embedding extraction: <200ms per 5-second audio sample
- Profile creation: <1 minute for 50 samples
- Verification: <500ms per sample
- Batch verification (100 files): <2 minutes

**Resource Monitoring:**
- Memory: Model should use <2GB RAM
- CPU: Utilize available cores for batch processing
- Disk I/O: Atomic writes should complete <100ms

### Accessibility Testing

**Manual Testing Checklist:**
- Keyboard navigation through all pages
- Screen reader compatibility (ARIA labels)
- Focus indicators visible
- Color contrast meets WCAG AA (4.5:1 for text)
- Form inputs have associated labels
- Error messages announced to screen readers

**Automated Accessibility:**
- Use axe-core for automated accessibility checks
- Run on each page component
- Verify no violations for WCAG 2.1 Level AA

### Testing Workflow

**Development:**
1. Write property tests alongside implementation
2. Run property tests with 100 iterations
3. Write unit tests for specific examples and error cases
4. Run unit tests with coverage reporting (target: >80%)

**Pre-Commit:**
1. Run all unit tests (fast)
2. Run linting and formatting checks
3. Run type checking (mypy for Python, TypeScript for frontend)

**CI Pipeline:**
1. Run all unit tests
2. Run property tests with 100 iterations
3. Run integration tests
4. Generate coverage report
5. Run accessibility checks
6. Performance regression tests (compare against baseline)

**Pre-Release:**
1. Full property test suite with 1000 iterations
2. End-to-end integration tests
3. Manual accessibility testing
4. Performance benchmarking
5. Security audit (input validation, path traversal)

### Test Data Management

**Synthetic Test Data:**
- Generated audio: sine waves, noise, combined
- Controlled for: duration, SNR, sample rate, channels

**Real Test Data:**
- VoxCeleb test set samples (10 speakers, 5 samples each)
- Used only for integration tests and model behavior validation
- Not used for property tests (too expensive)

**Test Profile Management:**
- Profiles created during tests stored in `test_profiles/` directory
- Cleanup after each test run
- Isolation: Each test uses unique profile names

This comprehensive testing strategy ensures that:
- Core logic is validated through property-based tests (100+ iterations)
- Specific scenarios and error cases are covered by unit tests
- System integration is validated through end-to-end tests
- UI is accessible and functional
- Performance meets requirements
- Security vulnerabilities are prevented
