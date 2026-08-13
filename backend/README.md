# VoicePrint Backend

FastAPI-based backend for voice biometric enrollment and verification using SpeechBrain ECAPA-TDNN.

## Setup

### 1. Create Python Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** Installing PyTorch and SpeechBrain may take several minutes. Ensure you have a stable internet connection.

### 3. Run the Server

```bash
python main.py
```

The server will start on `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
backend/
├── main.py           # FastAPI application entry point with CORS
├── config.py         # Application configuration
├── model.py          # ECAPA-TDNN model loader (singleton)
├── audio_utils.py    # Audio preprocessing utilities
├── embedding.py      # Embedding extraction and similarity
├── profile_store.py  # File-based profile persistence
└── requirements.txt  # Python dependencies
```

## Configuration

Configuration is centralized in `config.py`. Key settings:

- **Model**: SpeechBrain ECAPA-TDNN (`speechbrain/spkrec-ecapa-voxceleb`)
- **Storage**: Local filesystem (`profiles/` directory)
- **Sample Rate**: 16kHz (target for ECAPA-TDNN)
- **Threshold**: 0.7 (default verification threshold)
- **CORS**: Enabled for `http://localhost:5173` (Vite frontend)

## Dependencies

- **FastAPI**: Web framework for REST API
- **Uvicorn**: ASGI server
- **PyTorch**: Deep learning framework
- **SpeechBrain**: Pretrained ECAPA-TDNN model
- **torchaudio**: Audio loading and processing
- **numpy**: Numerical operations and embedding storage
- **ffmpeg-python**: Audio format conversion (WebM to WAV)

## Development

The application runs in reload mode by default, automatically restarting on code changes.
