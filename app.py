from flask import Flask, render_template, request, redirect, session, jsonify
from flask_cors import CORS
import requests
import sqlite3
import os

app = Flask(__name__)
CORS(app)
app.secret_key = "secret123"

API_KEY = "pub_92fc3f979a3a473ebd98acf361b82233"

# ---------------- DATABASE ----------------
def init_db():
    try:
        conn = sqlite3.connect("search.db")
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY,
                query TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                password TEXT
            )
        """)

        conn.commit()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print("Database Error:", e)

init_db()

bookmarks = []

# ---------------- HOME ----------------
@app.route("/")
def home():
    search = request.args.get("search")
    language = request.args.get("language", "en")

    if search:
        try:
            conn = sqlite3.connect("search.db")
            c = conn.cursor()
            c.execute("INSERT INTO history (query) VALUES (?)", (search,))
            conn.commit()
            conn.close()
        except Exception as e:
            print("History Save Error:", e)

    articles = []

    try:
        url = "https://newsdata.io/api/1/news"
        params = {
            "apikey": API_KEY,
            "language": language
        }

        if search:
            params["q"] = search
        else:
            params["country"] = "in"

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            articles = data.get("results", [])
        else:
            print("News API Error:", response.status_code, response.text)

    except Exception as e:
        print("Error:", e)

    return render_template("article.html", articles=articles, user=session.get("user"))

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            conn = sqlite3.connect("search.db")
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            conn.close()

            if user:
                session["user"] = username
                return redirect("/")
            else:
                return "Invalid login"

        except Exception as e:
            print("Login Error:", e)
            return "Login error occurred"

    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            conn = sqlite3.connect("search.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect("/login")

        except Exception as e:
            print("Register Error:", e)
            return "Registration error occurred"

    return render_template("register.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# ---------------- BOOKMARK ----------------
@app.route("/bookmark")
def bookmark():
    title = request.args.get("title")
    if title and title not in bookmarks:
        bookmarks.append(title)
    return redirect("/")

@app.route("/bookmarks")
def bookmarks_page():
    return render_template("bookmarks.html", bookmarks=bookmarks)

# ---------------- API TEST ----------------
@app.route("/api/news")
def api_news():
    return jsonify({
        "status": "success",
        "message": "Backend is running successfully"
    })

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
