"""
Voice Print Model Generator — Main Entry Point
Usage:
    python main.py --mode demo
    python main.py --mode train --data_dir data/samples
    python main.py --mode predict --audio path/to/audio.wav --model models/voice_print_model.pkl
"""
import argparse
import os
import sys
import numpy as np

from src.utils import print_banner, ensure_dir
from src.feature_extractor import FeatureExtractor
from src.model import VoicePrintModel
from src.train import train
from src.predict import predict_from_array


def run_demo():
    """
    Demo mode: synthesize fake speakers, train GMMs, and predict.
    Works without any real audio files or librosa installed.
    """
    print("\n[Demo] Running Voice Print Model Generator Demo...")
    print("[Demo] Generating synthetic voice features for 3 speakers...\n")

    np.random.seed(42)
    extractor = FeatureExtractor()
    model = VoicePrintModel(n_components=4)

    # Simulate 3 speakers with distinct MFCC-like distributions
    speaker_data = {
        "Alice": np.random.randn(300, extractor.feature_dim) + np.array([1.0] * extractor.feature_dim),
        "Bob":   np.random.randn(300, extractor.feature_dim) + np.array([-1.0] * extractor.feature_dim),
        "Carol": np.random.randn(300, extractor.feature_dim) + np.array([0.0, 2.0] * (extractor.feature_dim // 2)),
    }

    print("[Demo] Training speaker models...")
    for speaker, features in speaker_data.items():
        model.train_speaker(speaker, features)

    ensure_dir("models")
    model.save("models/demo_model.pkl")

    # Test prediction on each speaker's data
    print("\n[Demo] Testing predictions:")
    print("-" * 45)
    correct = 0
    for speaker, features in speaker_data.items():
        # Use a small random subset for testing
        test_features = features[:50] + np.random.randn(50, extractor.feature_dim) * 0.2
        predicted, scores = model.predict(test_features)
        status = "✓" if predicted == speaker else "✗"
        correct += (predicted == speaker)
        print(f"  {status} True: {speaker:8s} → Predicted: {predicted}")

    print("-" * 45)
    print(f"\n[Demo] Accuracy: {correct}/{len(speaker_data)} = {correct/len(speaker_data)*100:.0f}%")
    print(f"\n[Demo] Model info: {model}")
    print("\n[Demo] Complete! ✅")


def run_train(args):
    """Training mode."""
    if not os.path.isdir(args.data_dir):
        print(f"[ERROR] Data directory not found: {args.data_dir}")
        sys.exit(1)

    ensure_dir("models")
    model_path = args.model or "models/voice_print_model.pkl"
    train(
        data_dir=args.data_dir,
        model_save_path=model_path,
        n_components=args.n_components,
    )


def run_predict(args):
    """Prediction mode."""
    if not args.audio:
        print("[ERROR] --audio is required for predict mode.")
        sys.exit(1)
    if not os.path.isfile(args.audio):
        print(f"[ERROR] Audio file not found: {args.audio}")
        sys.exit(1)

    model_path = args.model or "models/voice_print_model.pkl"
    if not os.path.isfile(model_path):
        print(f"[ERROR] Model not found: {model_path}. Train first with --mode train.")
        sys.exit(1)

    model = VoicePrintModel.load(model_path)
    extractor = FeatureExtractor()
    audio = extractor.load_audio(args.audio)
    result = predict_from_array(audio, model)

    print(f"\n[Predict] Audio: {args.audio}")
    print(f"[Predict] Predicted Speaker : {result['predicted_speaker']}")
    print(f"[Predict] Confidence        : {result['confidence']:.2%}")
    print(f"[Predict] All Scores:")
    for spk, score in sorted(result["scores"].items(), key=lambda x: -x[1]):
        marker = " ◀" if spk == result["predicted_speaker"] else ""
        print(f"   {spk:20s}: {score:.4f}{marker}")


def main():
    print_banner()

    parser = argparse.ArgumentParser(
        description="Voice Print Model Generator — Speaker Recognition"
    )
    parser.add_argument(
        "--mode",
        choices=["demo", "train", "predict"],
        default="demo",
        help="Operation mode (default: demo)",
    )
    parser.add_argument("--data_dir", default="data/samples",
                        help="Directory with speaker audio subdirectories")
    parser.add_argument("--audio", help="Audio file path for prediction")
    parser.add_argument("--model", help="Path to model file (.pkl)")
    parser.add_argument("--n_components", type=int, default=16,
                        help="Number of GMM components (default: 16)")

    args = parser.parse_args()

    if args.mode == "demo":
        run_demo()
    elif args.mode == "train":
        run_train(args)
    elif args.mode == "predict":
        run_predict(args)


if __name__ == "__main__":
    main()
