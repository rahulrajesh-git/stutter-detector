import librosa
import numpy as np

def extract_features(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
        y, _ = librosa.effects.trim(y)  # Trim silence

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        delta = librosa.feature.delta(mfcc)
        delta2 = librosa.feature.delta(mfcc, order=2)
        zcr = librosa.feature.zero_crossing_rate(y=y)
        rms = librosa.feature.rms(y=y)

        # Tile ZCR and RMS to match shape of MFCCs (approximate matching)
        zcr = np.tile(zcr, (13, 1))
        rms = np.tile(rms, (13, 1))

        combined = np.vstack([mfcc, delta, delta2, zcr, rms])
        mean = np.mean(combined, axis=1)
        std = np.std(combined, axis=1)

        return np.concatenate([mean, std])

    except Exception as e:
        print(f"❌ Error extracting features from {file_path}: {e}")
        return None
