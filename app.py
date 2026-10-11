import os
import sqlite3
from datetime import date
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-for-real-deployment")
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")


def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    with connect_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                category TEXT NOT NULL,
                total_copies INTEGER NOT NULL DEFAULT 1,
                available_copies INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                member_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                return_date TEXT,
                status TEXT NOT NULL DEFAULT 'Issued',
                FOREIGN KEY(book_id) REFERENCES books(id),
                FOREIGN KEY(member_id) REFERENCES members(id)
            );
        """)
        admin = conn.execute("SELECT id, password FROM admins WHERE username = ?", ("admin",)).fetchone()
        if admin is None:
            conn.execute(
                "INSERT INTO admins(username, password) VALUES (?, ?)",
                ("admin", generate_password_hash("admin123"))
            )
        elif not admin["password"].startswith(("scrypt:", "pbkdf2:")):
            # Upgrade the plain-text demo password created by the earlier version.
            conn.execute(
                "UPDATE admins SET password = ? WHERE id = ?",
                (generate_password_hash(admin["password"]), admin["id"])
            )


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


@app.route("/")
def index():
    if "admin_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with connect_db() as conn:
            admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
        valid = False
        if admin:
            stored = admin["password"]
            try:
                valid = check_password_hash(stored, password)
            except (ValueError, TypeError):
                valid = False
            # Supports older databases whose demo password was stored as plain text.
            if not valid and stored == password:
                valid = True
                with connect_db() as conn:
                    conn.execute(
                        "UPDATE admins SET password = ? WHERE id = ?",
                        (generate_password_hash(password), admin["id"])
                    )
        if valid:
            session.clear()
            session["admin_id"] = admin["id"]
            session["username"] = admin["username"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    with connect_db() as conn:
        stats = {
            "books": conn.execute("SELECT COUNT(*) FROM books").fetchone()[0],
            "copies": conn.execute("SELECT COALESCE(SUM(total_copies), 0) FROM books").fetchone()[0],
            "available": conn.execute("SELECT COALESCE(SUM(available_copies), 0) FROM books").fetchone()[0],
            "members": conn.execute("SELECT COUNT(*) FROM members").fetchone()[0],
            "issued": conn.execute("SELECT COUNT(*) FROM transactions WHERE status = 'Issued'").fetchone()[0],
        }
        recent = conn.execute("""
            SELECT t.id, b.title, m.name AS member_name, t.issue_date, t.status
            FROM transactions t
            JOIN books b ON b.id = t.book_id
            JOIN members m ON m.id = t.member_id
            ORDER BY t.id DESC LIMIT 6
        """).fetchall()
    return render_template("dashboard.html", stats=stats, recent=recent)


@app.route("/books")
@login_required
def books():
    q = request.args.get("q", "").strip()
    with connect_db() as conn:
        if q:
            pattern = f"%{q}%"
            rows = conn.execute("""
                SELECT * FROM books
                WHERE title LIKE ? OR author LIKE ? OR category LIKE ?
                ORDER BY title
            """, (pattern, pattern, pattern)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM books ORDER BY title").fetchall()
    return render_template("books.html", books=rows, q=q)


@app.route("/books/add", methods=["GET", "POST"])
@login_required
def add_book():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category = request.form.get("category", "").strip()
        try:
            copies = int(request.form.get("total_copies", "1"))
        except ValueError:
            copies = 0
        if not title or not author or not category or copies < 1:
            flash("Enter all fields and use at least 1 copy.", "danger")
        else:
            with connect_db() as conn:
                conn.execute("""
                    INSERT INTO books(title, author, category, total_copies, available_copies)
                    VALUES (?, ?, ?, ?, ?)
                """, (title, author, category, copies, copies))
            flash("Book added successfully.", "success")
            return redirect(url_for("books"))
    return render_template("book_form.html", book=None, page_title="Add Book")


@app.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@login_required
def edit_book(book_id):
    with connect_db() as conn:
        book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if book is None:
            flash("Book not found.", "danger")
            return redirect(url_for("books"))
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            author = request.form.get("author", "").strip()
            category = request.form.get("category", "").strip()
            try:
                total = int(request.form.get("total_copies", "0"))
            except ValueError:
                total = 0
            currently_issued = book["total_copies"] - book["available_copies"]
            if not title or not author or not category or total < 1 or total < currently_issued:
                flash(f"Enter valid details. Total copies must be at least {max(1, currently_issued)}.", "danger")
            else:
                available = total - currently_issued
                conn.execute("""
                    UPDATE books SET title=?, author=?, category=?, total_copies=?, available_copies=?
                    WHERE id=?
                """, (title, author, category, total, available, book_id))
                flash("Book updated successfully.", "success")
                return redirect(url_for("books"))
    return render_template("book_form.html", book=book, page_title="Edit Book")


@app.route("/books/<int:book_id>/delete", methods=["POST"])
@login_required
def delete_book(book_id):
    with connect_db() as conn:
        history = conn.execute("SELECT COUNT(*) FROM transactions WHERE book_id = ?", (book_id,)).fetchone()[0]
        if history:
            flash("This book has transaction history, so it cannot be deleted. You can edit its details instead.", "warning")
        else:
            conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
            flash("Book deleted.", "success")
    return redirect(url_for("books"))


@app.route("/members", methods=["GET", "POST"])
@login_required
def members():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        if not name:
            flash("Member name is required.", "danger")
        else:
            with connect_db() as conn:
                conn.execute("INSERT INTO members(name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
            flash("Member registered successfully.", "success")
            return redirect(url_for("members"))
    q = request.args.get("q", "").strip()
    with connect_db() as conn:
        if q:
            pattern = f"%{q}%"
            rows = conn.execute("""
                SELECT * FROM members WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
                ORDER BY name
            """, (pattern, pattern, pattern)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM members ORDER BY name").fetchall()
    return render_template("members.html", members=rows, q=q)


@app.route("/transactions")
@login_required
def transactions():
    with connect_db() as conn:
        rows = conn.execute("""
            SELECT t.*, b.title AS book_title, m.name AS member_name
            FROM transactions t
            JOIN books b ON b.id = t.book_id
            JOIN members m ON m.id = t.member_id
            ORDER BY t.id DESC
        """).fetchall()
        books_list = conn.execute(
            "SELECT id, title, available_copies FROM books WHERE available_copies > 0 ORDER BY title"
        ).fetchall()
        members_list = conn.execute("SELECT id, name FROM members ORDER BY name").fetchall()
    return render_template("transactions.html", transactions=rows, books=books_list, members=members_list)


@app.route("/transactions/issue", methods=["POST"])
@login_required
def issue_book():
    try:
        book_id = int(request.form.get("book_id", "0"))
        member_id = int(request.form.get("member_id", "0"))
    except ValueError:
        flash("Choose a valid book and member.", "danger")
        return redirect(url_for("transactions"))
    with connect_db() as conn:
        book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        member = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
        if not book or not member:
            flash("Book or member not found.", "danger")
        elif book["available_copies"] < 1:
            flash("No copies of this book are currently available.", "warning")
        else:
            conn.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = ?", (book_id,))
            conn.execute("""
                INSERT INTO transactions(book_id, member_id, issue_date, status)
                VALUES (?, ?, ?, 'Issued')
            """, (book_id, member_id, date.today().isoformat()))
            flash("Book issued successfully.", "success")
    return redirect(url_for("transactions"))


@app.route("/transactions/<int:transaction_id>/return", methods=["POST"])
@login_required
def return_book(transaction_id):
    with connect_db() as conn:
        tx = conn.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,)).fetchone()
        if not tx:
            flash("Transaction not found.", "danger")
        elif tx["status"] == "Returned":
            flash("This book has already been returned.", "info")
        else:
            conn.execute("""
                UPDATE transactions SET status='Returned', return_date=? WHERE id=?
            """, (date.today().isoformat(), transaction_id))
            conn.execute(
                "UPDATE books SET available_copies = available_copies + 1 WHERE id = ?",
                (tx["book_id"],)
            )
            flash("Book returned successfully.", "success")
    return redirect(url_for("transactions"))


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
