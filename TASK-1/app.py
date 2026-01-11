from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re
import csv
import os

app = Flask(__name__)

CSV_FILE = "emails.csv"

@app.route("/", methods=["GET", "POST"])
def index():
    emails = []
    if request.method == "POST":
        url = request.form["url"]

        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()

            emails = set(re.findall(
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                text
            ))

            # CSV auto save
            file_exists = os.path.isfile(CSV_FILE)
            with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Website URL", "Email"])

                for email in emails:
                    writer.writerow([url, email])

        except Exception as e:
            return f"Error: {e}"

    return render_template("index.html", emails=emails)

if __name__ == "__main__":
    app.run(debug=True)
