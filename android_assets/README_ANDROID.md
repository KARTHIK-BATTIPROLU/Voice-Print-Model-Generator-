# Android Offline Voice Biometric Verification Guide

This directory contains the complete offline model assets to run voice biometric verification directly inside your Android app **without any API server**.

---

## Model & Asset Files

All files are located in the **[`android_assets/`](file:///c:/Users/Karthik/OneDrive/Desktop/Voice%20Print%20Model%20Generator/android_assets)** folder:

| File Name | Size | Type | Purpose |
| :--- | :--- | :--- | :--- |
| **`ecapa_tdnn_model.pt`** | **~83.5 MB** | **TorchScript Deep Learning Model** | PyTorch Mobile neural network model that extracts 192-dimensional embeddings directly from audio features on Android. |
| **`enrolled_voiceprint.json`** | **~3 KB** | **Enrolled Speaker Template** | The 192-float master voiceprint vector for **ASTA_primary** generated from your dataset. |
| **`enrolled_voiceprint.bin`** | **768 bytes** | **Binary Vector** | Fast binary representation of the 192-float voiceprint template. |

---

## How Offline Android Voice Biometrics Works

1. **Audio Recording**: Record a 16kHz mono audio clip on Android.
2. **Feature Extraction**: Compute 80-channel Log-Mel filterbank spectrogram features.
3. **Neural Network Embedding**: Pass features through **`ecapa_tdnn_model.pt`** via PyTorch Mobile to generate a live 192-float embedding.
4. **Cosine Similarity Check**: Compare live embedding against **`enrolled_voiceprint.json`**. If score $\ge 0.65 \implies$ **VERIFIED**.

---

## Android App Setup Instructions

### Step 1: Add Dependencies in `build.gradle` (Module: app)

```groovy
dependencies {
    // PyTorch Mobile for running ecapa_tdnn_model.pt offline
    implementation 'org.pytorch:pytorch_android_lite:1.13.1'
    implementation 'org.pytorch:pytorch_android_torchvision_lite:1.13.1'
}
```

### Step 2: Copy Models to Android Assets
Place both files into your Android project folder: `app/src/main/assets/`
- `app/src/main/assets/ecapa_tdnn_model.pt`
- `app/src/main/assets/enrolled_voiceprint.json`

---

## Kotlin Implementation Code

```kotlin
import android.content.Context
import org.json.JSONArray
import org.pytorch.IValue
import org.pytorch.Module
import org.pytorch.Tensor
import java.io.File
import java.io.FileOutputStream

class OfflineVoiceVerifier(private val context: Context) {

    private val module: Module by lazy {
        Module.load(assetFilePath(context, "ecapa_tdnn_model.pt"))
    }

    private val enrolledVoiceprint: FloatArray by lazy {
        loadEnrolledVoiceprint()
    }

    // Copy asset file to local internal storage path for PyTorch loader
    private fun assetFilePath(context: Context, assetName: String): String {
        val file = File(context.filesDir, assetName)
        if (file.exists() && file.length() > 0) return file.absolutePath
        context.assets.open(assetName).use { inputStream ->
            FileOutputStream(file).use { outputStream ->
                val buffer = ByteArray(4 * 1024)
                var read: Int
                while (inputStream.read(buffer).also { read = it } != -1) {
                    outputStream.write(buffer, 0, read)
                }
                outputStream.flush()
            }
        }
        return file.absolutePath
    }

    // Load enrolled voiceprint JSON array (192 floats)
    private fun loadEnrolledVoiceprint(): FloatArray {
        val jsonStr = context.assets.open("enrolled_voiceprint.json").bufferedReader().use { it.readText() }
        val jsonArray = JSONArray(jsonStr)
        return FloatArray(jsonArray.length()) { i -> jsonArray.getDouble(i).toFloat() }
    }

    // Extract 192-dim embedding from 80-mel filterbank features [1, num_frames, 80]
    fun extractEmbedding(features: Array<FloatArray>): FloatArray {
        val numFrames = features.size
        val flatFeatures = FloatArray(numFrames * 80)
        for (i in 0 until numFrames) {
            System.arraycopy(features[i], 0, flatFeatures, i * 80, 80)
        }

        // Shape: [1, num_frames, 80]
        val inputTensor = Tensor.fromBlob(flatFeatures, longArrayOf(1, numFrames.toLong(), 80))
        val outputTensor = module.forward(IValue.from(inputTensor)).toTensor()
        return outputTensor.dataAsFloatArray
    }

    // Calculate Cosine Similarity
    fun computeCosineSimilarity(a: FloatArray, b: FloatArray): Float {
        var dot = 0f
        var normA = 0f
        var normB = 0f
        for (i in a.indices) {
            dot += a[i] * b[i]
            normA += a[i] * a[i]
            normB += b[i] * b[i]
        }
        return if (normA == 0f || normB == 0f) 0f else (dot / (Math.sqrt(normA.toDouble()) * Math.sqrt(normB.toDouble()))).toFloat()
    }

    // Verify live recording against enrolled ASTA_primary voiceprint
    fun verifyUser(liveFeatures: Array<FloatArray>, threshold: Float = 0.65f): VerificationResult {
        val liveEmbedding = extractEmbedding(liveFeatures)
        val score = computeCosineSimilarity(liveEmbedding, enrolledVoiceprint)
        val isVerified = score >= threshold
        return VerificationResult(isVerified, score)
    }

    data class VerificationResult(val isVerified: Boolean, val score: Float)
}
```
