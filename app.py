import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS options (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            votes INTEGER DEFAULT 0,
            added_by TEXT DEFAULT 'Anonymous'
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, votes, added_by FROM options ORDER BY votes DESC")
    rows = cur.fetchall()
    cur.execute("SELECT COALESCE(SUM(votes), 0) FROM options")
    total_votes = cur.fetchone()[0]
    cur.close()
    conn.close()
    options = [{"name": r[0], "votes": r[1], "added_by": r[2]} for r in rows]
    return render_template("index.html", options=options, total=total_votes)


@app.route("/add", methods=["POST"])
def add_option():
    name = request.form.get("name", "").strip()
    username = request.form.get("username", "").strip()
    if name:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO options (name, added_by) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
            (name, username or "Anonymous"),
        )
        conn.commit()
        cur.close()
        conn.close()
    return redirect(url_for("index"))


@app.route("/vote/<name>", methods=["POST"])
def vote(name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE options SET votes = votes + 1 WHERE name = %s", (name,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("index"))



if not os.environ.get("TESTING"):
    with app.app_context():
        init_db()

if __name__ == "__main__":
    app.run(debug=True)
