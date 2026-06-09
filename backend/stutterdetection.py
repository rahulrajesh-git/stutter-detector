import os
import joblib
import numpy as np
import librosa
from sklearn.preprocessing import StandardScaler

# Constants
EXPECTED_FEATURE_SIZE = 130

# Use absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "logistic_regression", "logistic_regression_model.pkl")
scaler_mean_path = os.path.join(BASE_DIR, "logistic_regression", "logistic_regression_scaler_mean.npy")
scaler_scale_path = os.path.join(BASE_DIR, "logistic_regression", "logistic_regression_scaler_scale.npy")

# Load model and scaler
try:
    model = joblib.load(model_path)
    scaler = StandardScaler()
    scaler.mean_ = np.load(scaler_mean_path)
    scaler.scale_ = np.load(scaler_scale_path)
except Exception as e:
    raise RuntimeError(f" Failed to load model or scaler: {e}")

def extract_features(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
        y, _ = librosa.effects.trim(y)

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        delta = librosa.feature.delta(mfcc)
        delta2 = librosa.feature.delta(mfcc, order=2)
        zcr = librosa.feature.zero_crossing_rate(y=y)
        rms = librosa.feature.rms(y=y)

        # Tile to match shape of MFCCs
        zcr = np.tile(zcr, (mfcc.shape[0], 1))
        rms = np.tile(rms, (mfcc.shape[0], 1))

        combined = np.vstack([mfcc, delta, delta2, zcr, rms])
        mean = np.mean(combined, axis=1)
        std = np.std(combined, axis=1)

        return np.concatenate([mean, std])

    except Exception as e:
        print(f"❌ Error extracting features from {file_path}: {e}")
        return None


def analyze_stutter(file_path):
    try:
        features = extract_features(file_path)
        if features is None:
            return " Could not extract valid features from audio."

        if features.shape[0] != EXPECTED_FEATURE_SIZE:
            return f" Feature vector has unexpected shape: {features.shape[0]}"

        features_scaled = scaler.transform([features])
        prediction = model.predict(features_scaled)[0]

        try:
            proba = model.predict_proba(features_scaled)[0]
            confidence = proba[prediction]

            # Adjust label based on confidence
            if confidence < 0.86:
                label = " You are Stuttering! Take one more chance."
            else:
                label = " You are Stuttering! Take one more chance." if prediction == 1 else " You Sound Smooth."

            return f"{label} (Confidence: {confidence:.2f})"

        except AttributeError:
            # If model doesn't support predict_proba
            label = "🗣️ You are Stuttering! Take one more chance." if prediction == 1 else " You Sound Smooth."
            return f"{label} (Confidence score not available)"

    except Exception as e:
        print(f" Prediction failed for {file_path}: {e}")
        return f" Could not complete prediction: {str(e)}"
