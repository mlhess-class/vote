from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# In-memory store: list of {"name": str, "votes": int}
options = []


@app.route("/")
def index():
    sorted_options = sorted(options, key=lambda o: o["votes"], reverse=True)
    total_votes = sum(o["votes"] for o in options)
    return render_template("index.html", options=sorted_options, total=total_votes)


@app.route("/add", methods=["POST"])
def add_option():
    name = request.form.get("name", "").strip()
    if name and not any(o["name"].lower() == name.lower() for o in options):
        options.append({"name": name, "votes": 0})
    return redirect(url_for("index"))


@app.route("/vote/<name>", methods=["POST"])
def vote(name):
    for o in options:
        if o["name"] == name:
            o["votes"] += 1
            break
    return redirect(url_for("index"))


@app.route("/reset", methods=["POST"])
def reset():
    options.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
