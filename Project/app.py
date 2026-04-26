from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from groq import Groq
import os
import json
import re

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max upload

@app.after_request
def add_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    return response

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

def ask_groq(prompt, max_tokens=1024):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

def extract_text_from_file(file):
    """Extract text from PDF or Word file"""
    filename = file.filename.lower()

    if filename.endswith('.pdf'):
        import pdfplumber
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()

    elif filename.endswith('.docx'):
        import docx
        doc = docx.Document(file)
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        return text.strip()

    elif filename.endswith('.txt'):
        return file.read().decode('utf-8', errors='ignore').strip()

    else:
        return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    question = data.get("question", "")
    context = data.get("context", "")

    prompt = f"""You are an expert study assistant helping students learn. Answer the following question clearly and educationally.

Context (if provided): {context}

Question: {question}

Provide a clear, well-structured answer with examples where helpful. Use simple language suitable for students."""

    return jsonify({"answer": ask_groq(prompt)})

@app.route("/summarize", methods=["POST"])
def summarize_text():
    data = request.get_json()
    text = data.get("text", "")
    style = data.get("style", "concise")

    style_instructions = {
        "concise": "Provide a brief 3-5 sentence summary highlighting the key points.",
        "detailed": "Provide a comprehensive summary with all important details, organized with bullet points.",
        "bullet": "Summarize in 5-8 clear bullet points covering the main ideas.",
        "simple": "Explain this in very simple terms as if explaining to a 10-year-old."
    }

    prompt = f"""You are an expert at summarizing educational content for students.

Text to summarize:
{text}

Instructions: {style_instructions.get(style, style_instructions['concise'])}

Make the summary helpful for studying and retaining information."""

    return jsonify({"summary": ask_groq(prompt)})

@app.route("/summarize-file", methods=["POST"])
def summarize_file():
    """New route: accept file upload, extract text, then summarize"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    style = request.form.get('style', 'concise')

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Extract text
    text = extract_text_from_file(file)

    if text is None:
        return jsonify({"error": "Unsupported file type. Please upload PDF, DOCX, or TXT."}), 400

    if not text:
        return jsonify({"error": "Could not extract text from file. File may be empty or image-based."}), 400

    # Limit text to avoid token overflow (approx 12000 words)
    words = text.split()
    if len(words) > 12000:
        text = " ".join(words[:12000]) + "\n\n[Note: Document was truncated for processing]"

    style_instructions = {
        "concise": "Provide a brief 3-5 sentence summary highlighting the key points.",
        "detailed": "Provide a comprehensive summary with all important details, organized with bullet points.",
        "bullet": "Summarize in 5-8 clear bullet points covering the main ideas.",
        "simple": "Explain this in very simple terms as if explaining to a 10-year-old."
    }

    prompt = f"""You are an expert at summarizing educational content for students.

Text to summarize:
{text}

Instructions: {style_instructions.get(style, style_instructions['concise'])}

Make the summary helpful for studying and retaining information."""

    summary = ask_groq(prompt, max_tokens=1500)
    return jsonify({"summary": summary})

@app.route("/quiz", methods=["POST"])
def generate_quiz():
    data = request.get_json()
    topic = data.get("topic", "")
    num_questions = data.get("num_questions", 5)
    difficulty = data.get("difficulty", "medium")

    prompt = f"""You are an expert quiz creator for students. Generate a quiz about: {topic}

Requirements:
- Create exactly {num_questions} multiple choice questions
- Difficulty level: {difficulty}
- Each question must have exactly 4 options (A, B, C, D)
- Include one correct answer per question

Return ONLY valid JSON in this exact format (no extra text, no markdown, no backticks):
{{
  "quiz_title": "Quiz Title Here",
  "questions": [
    {{
      "id": 1,
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct_answer": "A",
      "explanation": "Brief explanation of why this is correct"
    }}
  ]
}}"""

    response_text = ask_groq(prompt, max_tokens=2048)
    response_text = re.sub(r'^```json\s*', '', response_text.strip())
    response_text = re.sub(r'^```\s*', '', response_text)
    response_text = re.sub(r'\s*```$', '', response_text)
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        quiz_data = json.loads(json_match.group())
    else:
        quiz_data = json.loads(response_text)

    return jsonify(quiz_data)

@app.route("/explain", methods=["POST"])
def explain_concept():
    data = request.get_json()
    concept = data.get("concept", "")
    level = data.get("level", "intermediate")

    prompt = f"""You are a brilliant teacher. Explain the concept: "{concept}"

Target audience level: {level}
- beginner: Use very simple words, analogies, and real-world examples
- intermediate: Standard explanation with some technical terms explained
- advanced: In-depth explanation with technical details

Structure your explanation with:
1. Simple definition
2. Key points (use bullet points)
3. A memorable analogy or real-world example
4. Why it matters / applications

Make it engaging and easy to remember."""

    return jsonify({"explanation": ask_groq(prompt)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
