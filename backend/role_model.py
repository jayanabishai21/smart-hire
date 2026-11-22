import re
from pathlib import Path
import joblib

MODEL_DIR = Path(__file__).parent / "models"
model = joblib.load(MODEL_DIR / "role_model.pkl")
tfidf = joblib.load(MODEL_DIR / "tfidf.pkl")


# This MUST be the same cleaning function used in Colab
def clean_for_model(text):
    text = text.lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def predict_roles(text, top_n=4):
    vec = tfidf.transform([clean_for_model(text)])
    probs = model.predict_proba(vec)[0]
    top = probs.argsort()[-top_n:][::-1]
    return [{"role": model.classes_[i], "confidence": round(float(probs[i]) * 100)}
            for i in top]