from flask import Flask, render_template, request, redirect, session
import requests
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

API_KEY = "pub_92fc3f979a3a473ebd98acf361b82233"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("search.db")
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, query TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS bookmarks (id INTEGER PRIMARY KEY, title TEXT)")

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    search = request.args.get("search")
    language = request.args.get("language", "en")

    articles = []

    try:
        url = "https://newsdata.io/api/1/news"

        params = {
            "apikey": API_KEY,
            "language": language,
        }

        if search:
            params["q"] = search

            # save search history
            conn = sqlite3.connect("search.db")
            c = conn.cursor()
            c.execute("INSERT INTO history (query) VALUES (?)", (search,))
            conn.commit()
            conn.close()
        else:
            params["country"] = "in"

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()

            if "results" in data:
                articles = data["results"]
            else:
                print("No results found:", data)

        else:
            print("API Error:", response.status_code)

    except Exception as e:
        print("Error:", e)

    return render_template("index.html", articles=articles, user=session.get("user"))

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

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

    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("search.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        return redirect("/login")

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

    if title:
        conn = sqlite3.connect("search.db")
        c = conn.cursor()
        c.execute("INSERT INTO bookmarks (title) VALUES (?)", (title,))
        conn.commit()
        conn.close()

    return redirect("/")

@app.route("/bookmarks")
def bookmarks_page():
    conn = sqlite3.connect("search.db")
    c = conn.cursor()
    c.execute("SELECT title FROM bookmarks")
    data = c.fetchall()
    conn.close()

    bookmarks = [i[0] for i in data]

    return render_template("bookmarks.html", bookmarks=bookmarks)

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
