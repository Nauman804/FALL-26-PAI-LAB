from flask import Flask, render_template, request
import json
import random
import numpy as np
import faiss
import os
from sentence_transformers import SentenceTransformer

# Cache folder
os.environ['HF_HOME'] = './model_cache'

app = Flask(__name__)

# ---------------- LOAD DATA ----------------
with open("intents.json", "r", encoding="utf-8") as file:
    data = json.load(file)

patterns = []
intent_responses = []

for intent in data["intents"]:
    for pattern in intent["patterns"]:
        patterns.append(pattern)
        intent_responses.append(intent["responses"])

print("Loading AI Model... Please wait.")

# ---------------- MODEL FIX ----------------
try:
    # Try offline model first
    model = SentenceTransformer(
        './model_cache/paraphrase-MiniLM-L6-v2',
        local_files_only=True
    )
    print("✅ Model loaded from local cache")

except:
    print("⬇️ Loading lightweight model (no Hugging Face error)...")

    # SAFE MODEL (no 429 issue)
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("✅ Model loaded successfully")

# ---------------- FAISS SETUP ----------------
embeddings = model.encode(patterns, normalize_embeddings=True).astype('float32')

dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# ---------------- CHATBOT FUNCTION ----------------
def chatbot_response(user_input):
    query_vec = model.encode([user_input], normalize_embeddings=True).astype('float32')

    distances, indices = index.search(query_vec, k=1)

    best_match_idx = indices[0][0]
    best_distance = distances[0][0]

    print(f"\nUser: {user_input}")
    print(f"Distance: {best_distance:.2f}")
    print(f"Match: {patterns[best_match_idx]}\n")

    if best_distance > 1.0:
        return "Sorry 😕 I don't understand that. Try asking about admissions, courses, or fees."

    return random.choice(intent_responses[best_match_idx])

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def get_bot_response():
    user_text = request.form["msg"]
    return chatbot_response(user_text)

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=False)