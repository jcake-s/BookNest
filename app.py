import os
from datetime import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///booknest.db")

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    """Dashboard: show current book, top-voted suggestions, recent discussions."""
    user_id = session["user_id"]

    current = db.execute("SELECT * FROM books WHERE status = 'reading' LIMIT 1")

    suggestions = db.execute(
        "SELECT b. *, COUNT(v.id) AS votes "
        "FROM books b LEFT JOIN votes v ON b.id = v.book_id "
        "WHERE b.status = 'suggested' "
        "GROUP BY b.id ORDER BY votes DESC LIMIT 5"
    )

    recent = db.execute(
        "SELECT d. *, u.username, b.title FROM discussions d "
        "JOIN users u ON d.user_id = u.id "
        "JOIN books b ON d.book_id = b.id "
        "ORDER BY d.created_at DESC LIMIT 5"
    )

    return render_template("index.html",
                           current=current[0] if current else None,
                           suggestions=suggestions,
                           recent=recent)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("Must provide username", 400)
        if not password:
            return apology("Must provide password", 400)
        if password != confirmation:
            return apology("Passwords do not match", 400)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))

        except:
            return apology("Username already taken", 400)

        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("Must provide username", 403)
        if not password:
            return apology("Must provide password", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("Invalid username or password", 403)

        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/suggest", methods=["GET", "POST"])
@login_required
def suggest():
    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        description = request.form.get("description")

        if not title:
            return apology("Must provide title", 400)
        if not author:
            return apology("Must provide author", 400)

        db.execute(
            "INSERT INTO books (title, author, description, suggested_by) "
            "VALUES (?, ?, ?, ?)",
            title, author, description, session["user_id"]
        )
        return redirect("/books")
    return render_template("suggest.html")

@app.route("/books")
@login_required
def books():
    rows = db.execute(
        "SELECT b.*, u.username AS suggester, "
        "COUNT(v.id) AS votes "
        "FROM books b "
        "JOIN users u ON b.suggested_by = u.id "
        "LEFT JOIN votes v ON b.id = v.book_id "
        "GROUP BY b.id "
        "ORDER BY votes DESC, b.created_at DESC"
    )
    return render_template("books.html", books=rows)

@app.route("/vote/<int:book_id>", methods=["POST"])
@login_required
def vote(book_id):
    user_id = session["user_id"]
    existing = db.execute(
        "SELECT id FROM votes WHERE user_id = ? AND book_id = ?",
        user_id, book_id
    )
    if existing:
        db.execute("DELETE FROM votes WHERE user_id = ? AND book_id = ?",
                   user_id, book_id)
    else:
        db.execute("INSERT INTO votes (user_id, book_id) VALUES (?, ?)",
                   user_id, book_id)
    return redirect("/books")

@app.route("/book/<int:book_id>")
@login_required
def book(book_id):
    rows = db.execute("SELECT * FROM books WHERE id = ?", book_id)
    if not rows:
        return apology("Book not found", 404)

    discussions = db.execute(
        "SELECT d.*, u.username FROM discussions d "
        "JOIN users u ON d.user_id = u.id "
        "WHERE d.book_id = ? ORDER BY d.created_at DESC",
        book_id
    )
    return render_template("book.html", book=rows[0], discussions=discussions)

@app.route("/discuss/<int:book_id>", methods=["POST"])
@login_required
def discuss(book_id):
    content = request.form.get("content")
    if not content:
        return apology("Message cannot be empty", 400)

    db.execute(
        "INSERT INTO discussions (book_id, user_id, content) VALUES (?, ?, ?)",
        book_id, session["user_id"], content
    )
    return redirect(f"/book/{book_id}")

@app.route("/mark-reading/<int:book_id>", methods=["POST"])
@login_required
def mark_reading(book_id):
    """Set this book as the current 'reading' book; mark others as finished."""
    db.execute("UPDATE books SET status = 'finished' WHERE status = 'reading'")
    db.execute("UPDATE books SET status = 'reading' WHERE id = ?", book_id)
    return redirect(f"/book/{book_id}")

@app.route("/delete/<int:book_id>", methods=["POST"])
@login_required
def delete_book(book_id):
    """Deletea suggested book (only by the user who suggested it)."""
    user_id = session["user_id"]

    rows = db.execute("SELECT * FROM books WHERE id = ?", book_id)
    if not rows:
        return apology("Book not found", 404)

    book = rows[0]

    if book["suggested_by"] != user_id:
        return apology("You can only delete books you suggested", 403)

    if book["status"] == "reading":
        return apology("Cannot delete the book currently being read", 400)

    db.execute("DELETE FROM votes WHERE book_id = ?", book_id)
    db.execute("DELETE FROM discussions WHERE book_id = ?", book_id)

    db.execute("DELETE FROM books WHERE id = ?", book_id)

    return redirect("/books")

@app.route("/profile/<username>")
@login_required
def profile(username):
    """Show a user's profile and their contributions."""
    rows = db.execute("SELECT id, username, created_at FROM users WHERE username = ?", username)
    if not rows:
        return apology("User not found", 404)

    user = rows[0]
    user_id = user["id"]

    suggested = db.execute(
        "SELECT b.*, "
        "(SELECT COUNT(*) FROM votes v WHERE v.book_id = b.id) AS votes "
        "FROM books b WHERE b.suggested_by = ? "
        "ORDER BY b.created_at DESC",
        user_id
    )

    voted = db.execute(
        "SELECT b.id, b.title, b.author, v.created_at "
        "FROM votes v "
        "JOIN books b ON v.book_id = b.id "
        "WHERE v.user_id = ? "
        "ORDER BY v.created_at DESC",
        user_id
    )

    messages = db.execute(
        "SELECT d.content, d.created_at, d.book_id, b.title "
        "FROM discussions d "
        "JOIN books b ON d.book_id = b.id "
        "WHERE d.user_id = ? "
        "ORDER BY d.created_at DESC",
        user_id
    )

    stats = {
        "suggested": len(suggested),
        "voted": len(voted),
        "messages": len(messages),
    }

    return render_template(
        "profile.html",
        profile_user=user,
        suggested=suggested,
        voted=voted,
        messages=messages,
        stats=stats,
        is_own_profile=(session["user_id"] == user_id),
    )

@app.route("/mark-finished/<int:book_id>", methods=["POST"])
@login_required
def mark_finished(book_id):
    """Mark a book as finished reading."""
    rows = db.execute("SELECT * FROM books WHERE id = ?", book_id)
    if not rows:
        return apology("Book not found", 404)

    db.execute("UPDATE books SET status = 'finished' WHERE id = ?", book_id)
    return redirect(f"/book/{book_id}")
