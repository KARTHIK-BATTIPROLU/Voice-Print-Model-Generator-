# Voice Print Model Generator 🎙️

A Python-based Voice Print (Speaker Recognition) Model Generator that extracts voice features (MFCCs) and builds speaker identification models.

## Features
- Extract MFCC features from audio files
- Train a GMM-based speaker recognition model
- Evaluate and test speaker identification
- Generate voice print embeddings

## Project Structure
```
VoicePrintModel/
├── src/
│   ├── feature_extractor.py   # MFCC & audio feature extraction
│   ├── model.py               # GMM speaker model
│   ├── train.py               # Training pipeline
│   ├── predict.py             # Prediction / inference
│   └── utils.py               # Helper utilities
├── data/
│   └── samples/               # Place audio samples here (.wav)
├── models/                    # Saved trained models
├── main.py                    # Entry point
├── requirements.txt
└── README.md
```

## Installation
```bash
pip install -r requirements.txt
```

## Usage

### Train a model
```bash
python main.py --mode train --data_dir data/samples
```

### Predict speaker
```bash
python main.py --mode predict --audio path/to/audio.wav
```

### Run demo
```bash
python main.py --mode demo
```

## Requirements
- Python 3.8+
- See `requirements.txt` for dependencies

## How It Works
1. Audio files are loaded and preprocessed
2. MFCC features are extracted from each audio segment
3. A Gaussian Mixture Model (GMM) is trained per speaker
4. During prediction, the model scores the audio against all speaker GMMs
5. The speaker with the highest log-likelihood is returned
