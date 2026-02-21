from flask import Flask, render_template

app = Flask(__name__, template_folder='templates')

with app.app_context():
    html = render_template('index.html')
    print(html)
