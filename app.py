from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Docker Swarm service names
AUTH_URL = "http://auth:5001"
BOOK_URL = "http://books:5002"
BORROW_URL = "http://borrow:5003"


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("books"))
    return redirect(url_for("signin"))


# ---------- AUTH ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = {
            "name": request.form["name"],
            "email": request.form["email"],
            "password": request.form["password"]
        }

        try:
            res = requests.post(
                f"{AUTH_URL}/signup",
                json=data,
                timeout=10
            )

            if res.status_code == 201:
                flash("Signup successful!", "success")
                return redirect(url_for("signin"))
            else:
                flash("Signup failed", "danger")

        except requests.exceptions.RequestException as e:
            app.logger.error("Authentication service error: %s", e)
            flash("Authentication service is unavailable. Please try again.", "danger")

    return render_template("signup.html")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        data = {
            "email": request.form["email"],
            "password": request.form["password"]
        }

        try:
            res = requests.post(
                f"{AUTH_URL}/signin",
                json=data,
                timeout=10
            )

            if res.status_code == 200:
                user = res.json()
                session["user_id"] = user["user_id"]
                session["name"] = user["name"]
                return redirect(url_for("books"))
            else:
                flash("Invalid credentials", "danger")

        except requests.exceptions.RequestException as e:
            app.logger.error("Authentication service error: %s", e)
            flash("Authentication service is unavailable. Please try again.", "danger")

    return render_template("signin.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("signin"))


# ---------- BOOKS ----------
@app.route("/books")
def books():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    try:
        res = requests.get(f"{BOOK_URL}/books", timeout=10)
        res.raise_for_status()
        return render_template("books.html", books=res.json())

    except requests.exceptions.RequestException as e:
        app.logger.error("Book service error: %s", e)
        flash("Book service is unavailable. Please try again.", "danger")
        return render_template("books.html", books=[])


# ---------- BORROW ----------
@app.route("/borrow/<int:book_id>")
def borrow(book_id):
    if "user_id" not in session:
        return redirect(url_for("signin"))

    data = {
        "user_id": session["user_id"],
        "book_id": book_id
    }

    try:
        res = requests.post(
            f"{BORROW_URL}/borrow",
            json=data,
            timeout=10
        )

        if res.status_code == 201:
            flash("Book borrowed!", "success")
        else:
            flash("Unable to borrow this book.", "danger")

    except requests.exceptions.RequestException as e:
        app.logger.error("Borrow service error: %s", e)
        flash("Borrow service is unavailable. Please try again.", "danger")

    return redirect(url_for("books"))


@app.route("/mybooks")
def mybooks():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    try:
        res = requests.get(
            f"{BORROW_URL}/mybooks/{session['user_id']}",
            timeout=10
        )
        res.raise_for_status()
        return render_template("borrow.html", books=res.json())

    except requests.exceptions.RequestException as e:
        app.logger.error("Borrow service error: %s", e)
        flash("Unable to retrieve your borrowed books.", "danger")
        return render_template("borrow.html", books=[])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
