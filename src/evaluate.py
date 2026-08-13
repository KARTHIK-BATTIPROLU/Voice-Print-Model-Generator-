"""
Evaluation module for Voice Print Model Generator.
Provides accuracy metrics, confusion matrix, and EER (Equal Error Rate).
"""
import numpy as np
from typing import Dict, List, Tuple


def compute_accuracy(
    model,
    speaker_features: Dict[str, np.ndarray],
    normalize: bool = True,
) -> Dict:
    """
    Compute speaker identification accuracy on a feature dict.

    Args:
        model:             Trained VoicePrintModel.
        speaker_features:  {speaker_id: feature_matrix} dict.
        normalize:         Whether to normalize features.

    Returns:
        dict with accuracy, per-speaker results, confusion matrix.
    """
    from src.utils import normalize_features

    true_labels = []
    pred_labels = []

    per_speaker = {}
    for speaker, features in speaker_features.items():
        if normalize:
            features = normalize_features(features)

        predicted, scores = model.predict(features)
        correct = predicted == speaker

        per_speaker[speaker] = {
            "predicted": predicted,
            "correct": correct,
            "scores": scores,
        }
        true_labels.append(speaker)
        pred_labels.append(predicted)

    total = len(true_labels)
    correct_count = sum(t == p for t, p in zip(true_labels, pred_labels))
    accuracy = correct_count / total if total > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "correct": correct_count,
        "total": total,
        "per_speaker": per_speaker,
    }


def compute_eer(target_scores: List[float], impostor_scores: List[float]) -> Tuple[float, float]:
    """
    Compute Equal Error Rate (EER) for binary speaker verification.

    Args:
        target_scores:   Log-likelihood scores for genuine (same-speaker) trials.
        impostor_scores: Log-likelihood scores for impostor (different-speaker) trials.

    Returns:
        (eer, threshold) — EER value and corresponding threshold.
    """
    all_scores = np.array(target_scores + impostor_scores)
    thresholds = np.linspace(all_scores.min(), all_scores.max(), 500)

    best_eer = 1.0
    best_threshold = 0.0

    for thresh in thresholds:
        fa = np.mean(np.array(impostor_scores) >= thresh)   # False Accept Rate
        fr = np.mean(np.array(target_scores) < thresh)      # False Reject Rate
        eer_candidate = abs(fa - fr)
        if eer_candidate < abs(best_eer - 0.5):
            best_eer = (fa + fr) / 2
            best_threshold = thresh

    return round(float(best_eer), 4), round(float(best_threshold), 4)


def print_evaluation_report(results: Dict) -> None:
    """Pretty-print evaluation results."""
    print("\n" + "=" * 50)
    print("  EVALUATION REPORT")
    print("=" * 50)
    print(f"  Overall Accuracy : {results['accuracy']:.2%}  "
          f"({results['correct']}/{results['total']})")
    print("-" * 50)
    print(f"  {'Speaker':<15} {'Predicted':<15} {'Result'}")
    print("-" * 50)
    for spk, res in results["per_speaker"].items():
        status = "✓ CORRECT" if res["correct"] else "✗ WRONG"
        print(f"  {spk:<15} {res['predicted']:<15} {status}")
    print("=" * 50)
