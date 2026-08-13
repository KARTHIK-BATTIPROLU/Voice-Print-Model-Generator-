# VoicePrint - Voice Biometric Platform

**A fully local, zero-cloud voice biometric platform for speaker enrollment and verification.**

VoicePrint enables users to create unique voiceprints from voice samples and verify speaker identity through real-time microphone input or batch audio file processing. Built with SpeechBrain's pretrained ECAPA-TDNN model for embedding extraction and cosine similarity scoring.

## 🎯 Features

- **Voice Enrollment**: Upload 10-500 WAV files to generate a personal voiceprint
- **Real-Time Verification**: Verify identity via microphone with animated waveform visualization
- **Batch Testing**: Test multiple audio clips against saved voiceprints with visual score output
- **Fully Local**: Zero cloud dependencies, all processing happens on your machine
- **Dark Theme UI**: Modern, accessible interface with electric violet accent

## 🏗️ Architecture

```
Backend (Python/FastAPI)          Frontend (React/Vite)
├── Model Loader (Singleton)      ├── Dashboard
├── Audio Processing              ├── Enrollment Page
├── Embedding Engine              ├── Verify Live Page
├── Profile Store                 └── Verify Batch Page
└── REST API + WebSocket
```

**Core Model**: SpeechBrain ECAPA-TDNN (`speechbrain/spkrec-ecapa-voxceleb`)
**Storage**: File-based (profiles/{name}/voiceprint.npy + meta.json)

## 📋 System Requirements

- **Python**: 3.10 or higher
- **Node.js**: 18 or higher
- **FFmpeg**: For audio format conversion
  - Windows: `choco install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt-get install ffmpeg`

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/KARTHIK-BATTIPROLU/Voice-Print-Model-Generator-.git
cd Voice-Print-Model-Generator-

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install

# Return to root
cd ..
```

### Running the Application

**Option 1: Using start script (Recommended)**
```bash
bash start.sh
```

**Option 2: Manual start**
```bash
# Terminal 1: Start backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

Access the application:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📖 How It Works

### Enrollment Process

1. **Upload Voice Samples** (10-500 WAV files)
   - System validates format, sample rate, duration
   - Resamples to 16kHz mono format
   - Filters low-quality samples (SNR < 5dB)

2. **Extract Embeddings**
   - ECAPA-TDNN model extracts 192-dimensional embeddings
   - Each embedding is L2-normalized to unit vector
   - Outliers detected using z-score method (2.5σ threshold)

3. **Generate Voiceprint**
   - Compute element-wise mean of all normalized embeddings
   - L2-normalize the averaged embedding
   - Calculate intra-class statistics for threshold suggestion

4. **Save Profile**
   - Store voiceprint as `profiles/{name}/voiceprint.npy`
   - Save metadata as `profiles/{name}/meta.json`

### Verification Process

1. **Capture/Upload Audio**
   - Live: Record via microphone (WebM → WAV conversion)
   - Batch: Upload multiple WAV files

2. **Extract Embedding**
   - Preprocess audio (resample, mono conversion)
   - Extract embedding using ECAPA-TDNN
   - L2-normalize embedding

3. **Compute Similarity**
   - Calculate cosine similarity with stored voiceprint
   - Compare against threshold (default: 0.7)
   - Return score and pass/fail result

**Similarity Scores:**
- Same speaker: typically >0.8
- Different speaker: typically <0.5
- Threshold: configurable per profile

## 🔧 Configuration

Configuration is stored in `backend/config.py`:

```python
model_path = "speechbrain/spkrec-ecapa-voxceleb"
storage_path = "profiles"
default_threshold = 0.7
target_sample_rate = 16000
min_snr_db = 5.0
min_duration_sec = 1.5
max_file_size_mb = 50
```

### Tuning the Threshold

The system suggests a threshold based on intra-class similarity:
```
suggested_threshold = mean_similarity - 2 * std_similarity
```

**Adjust threshold if:**
- Too many false rejections: Lower threshold (e.g., 0.65)
- Too many false acceptances: Raise threshold (e.g., 0.75)

## 🎨 Design System

**Color Palette:**
- Background: `#0A0A0F` (deep space black)
- Accent: `#6C63FF` (electric violet)
- Success: `#00D9A3` (teal green)
- Error: `#FF6B6B` (coral red)

**Typography:**
- Display: Space Grotesk
- Body: Inter
- Technical: JetBrains Mono

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 🐛 Troubleshooting

### Model Download Fails
**Issue**: SpeechBrain model download timeout or fails
**Solution**: 
```bash
# Pre-download model
python -c "from speechbrain.pretrained import EncoderClassifier; EncoderClassifier.from_hparams('speechbrain/spkrec-ecapa-voxceleb', savedir='pretrained_models/spkrec-ecapa-voxceleb')"
```

### Microphone Not Detected
**Issue**: Browser doesn't request microphone permission
**Solution**:
- Use HTTPS or localhost (required for mic access)
- Check browser permissions: Settings → Privacy → Microphone
- Try different browser (Chrome/Edge recommended)

### Score Always 0
**Issue**: All verification scores return 0.0
**Solution**:
- Ensure audio is >1.5 seconds
- Check audio isn't silence
- Verify enrollment completed successfully
- Restart backend server

### FFmpeg Not Found
**Issue**: WebM to WAV conversion fails
**Solution**:
- Install FFmpeg (see System Requirements)
- Verify installation: `ffmpeg -version`
- Add FFmpeg to system PATH

## 📊 API Endpoints

### Enrollment
```http
POST /api/enroll
Content-Type: multipart/form-data

profile_name: string
files: File[] (10-500 WAV files)
```

### Verification
```http
POST /api/verify
Content-Type: multipart/form-data

profile_name: string
audio: File (WAV or WebM)
```

### Profile Management
```http
GET    /api/profiles           # List all profiles
GET    /api/profiles/{name}    # Get profile metadata
DELETE /api/profiles/{name}    # Delete profile
PATCH  /api/profiles/{name}/threshold  # Update threshold
```

### Health Check
```http
GET /api/health
```

## ⚠️ Known Limitations

- **Not a Security System**: VoicePrint is designed for convenience, not high-security authentication
- **Recording Conditions**: Works best with consistent recording environment and equipment
- **Model Limitations**: Accuracy depends on voice sample quality and diversity
- **No Anti-Spoofing**: Does not detect recorded/synthetic voice playback
- **Language Independent**: Model trained on VoxCeleb (multilingual)

## 🛠️ Technology Stack

**Backend:**
- FastAPI 0.115.0
- PyTorch 2.4.0
- SpeechBrain 1.0.0
- torchaudio 2.4.0
- numpy 1.26.4

**Frontend:**
- React 18
- Vite 5.4
- Web Audio API
- Custom CSS (no UI libraries)

## 📁 Project Structure

```
voiceprint/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── model.py             # Singleton model loader
│   ├── audio_utils.py       # Audio preprocessing
│   ├── embedding.py         # Embedding extraction
│   ├── profile_store.py     # File-based persistence
│   ├── config.py            # Configuration
│   ├── requirements.txt
│   └── profiles/            # Auto-created profile storage
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/             # API client
│   │   ├── pages/           # Dashboard, Enroll, Verify pages
│   │   ├── components/      # Reusable UI components
│   │   └── styles/          # CSS variables
│   ├── package.json
│   └── vite.config.js
├── .kiro/specs/voiceprint/  # Implementation specifications
├── start.sh                 # Single-command startup script
└── README.md
```

## 📜 License

This project is part of the ASTA voice biometric gate for speaker verification pipeline.

## 🤝 Contributing

Contributions welcome! Please follow the spec-driven development workflow:
1. Check `.kiro/specs/voiceprint/` for requirements and design
2. Update tasks.md with new tasks
3. Implement with tests
4. Submit PR with requirement references

## 📞 Support

For issues and questions:
- GitHub Issues: https://github.com/KARTHIK-BATTIPROLU/Voice-Print-Model-Generator-/issues
- Email: [Contact repository owner]

---

**Generated for ASTA Project** - Voice Biometric Gate for Speaker Verification Pipeline  
Stack: SpeechBrain ECAPA-TDNN · FastAPI · React · Fully Local · Zero Cloud
