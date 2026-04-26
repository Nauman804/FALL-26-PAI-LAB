🎓 AI Study Assistant

Your personal AI tutor — ask questions, get summaries, quizzes, and explanations in one place.

📌 Overview

AI Study Assistant is a web-based application built with Flask and powered by Groq’s Llama 3.3 model. It helps students learn faster by providing instant answers, summaries, quizzes, and concept explanations.

✨ Features
💬 Ask AI – Get clear answers to any study-related question
📄 Summarize – Generate summaries from text, PDF, or Word files
🎯 Quiz Me – Create MCQ quizzes on any topic
💡 Explain – Learn concepts at different difficulty levels
🛠 Tech Stack
Backend: Python, Flask
AI Model: Llama 3.3 (via Groq API)
Frontend: HTML, CSS (Glassmorphism UI), JavaScript
File Processing: pdfplumber, python-docx
🚀 Installation & Setup
1. Clone the Repository
git clone https://github.com/Nauman804/ai_study_assistant.git
cd ai_study_assistant
2. Create Virtual Environment
python -m venv venv
3. Activate Environment
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
4. Install Dependencies
pip install -r requirements.txt
5. Add API Key



Create a .env file and add:

GROQ_API_KEY=your_api_key_here


6. Run the App
python app.py


8. Open in Browser
http://localhost:5000


📁 Project Structure
ai_study_assistant/
│
├── app.py
├── requirements.txt
├── .env
│
├── templates/
│   └── index.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── main.js





        
🔌 API Endpoints
Endpoint	Method	Description
/	GET	Main page
/ask	POST	Answer questions
/summarize	POST	Summarize text
/summarize-file	POST	Summarize files
/quiz	POST	Generate quiz
/explain	POST	Explain concepts





🎯 Use Cases


Students preparing for exams
Quick revision and summaries
Self-assessment using quizzes
Understanding difficult topics



⚠️ Notes
Make sure your API key is valid
Requires Python 3.10+




❤️ Contribution

Feel free to fork this repository and improve the project. Contributions are welcome!

📜 License

This project is free to use for educational purposes.
