from flask import Flask, render_template, request
import json
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load data
with open("intents.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Prepare corpus
corpus = []
responses = []

for intent in data["intents"]:
    for pattern in intent["patterns"]:
        corpus.append(pattern)
        responses.append(intent["responses"])

# Vectorizer
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(corpus)

def chatbot_response(user_input):
    user_vec = vectorizer.transform([user_input])
    similarity = cosine_similarity(user_vec, X)
    index = similarity.argmax()

    if similarity[0][index] < 0.3:
        return "Sorry 😕 I didn't understand. Try asking about admissions, fees, or programs."

    return random.choice(responses[index])


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get", methods=["POST"])
def get_bot_response():
    user_text = request.form["msg"]
    return chatbot_response(user_text)


if __name__ == "__main__":
    app.run(debug=True)