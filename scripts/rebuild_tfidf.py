import json
import pickle
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer

with open("artifacts/movies.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

corpus = [
    f"{m['title']} {m.get('year', '')} {' '.join(m.get('genres', []))} {m.get('directors', '')} {m.get('actors', '')} {m.get('overview', '')}"
    for m in movies
]

vec = TfidfVectorizer(max_features=5000, stop_words="english")
mat = vec.fit_transform(corpus)

with open("artifacts/tfidf_vectorizer.pkl", "wb") as f:
    pickle.dump(vec, f)

with open("artifacts/tfidf_matrix.pkl", "wb") as f:
    pickle.dump(mat, f)

with open("artifacts/tfidf_vectorizer.pkl", "rb") as f:
    vec_h = hashlib.sha256(f.read()).hexdigest()

with open("artifacts/tfidf_matrix.pkl", "rb") as f:
    mat_h = hashlib.sha256(f.read()).hexdigest()

with open("artifacts/manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

manifest["sha256"]["tfidf_vectorizer.pkl"] = vec_h
manifest["sha256"]["tfidf_matrix.pkl"] = mat_h

with open("artifacts/manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print("Updated TF-IDF artifacts and manifest sha256 successfully!")
