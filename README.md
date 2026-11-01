# BookNest

BookNest is a web application for a small book readers club to decide what to read next, discuss books together, and keep a running record of the club's reading history. It was built as the final project for CS50x.

The idea is simple: a book club needs a shared place to suggest books, vote on what to read next, and talk about the current book. Instead of juggling a group chat, a spreadsheet, and a pile of screenshots, BookNest puts all of that in a single, clean web app.

---

# Video Demo

https://www.youtube.com/watch?v=W3yWDebGyCs

---

# Features

## Accounts
- Register with a username and password (hashed with Werkzeug's `generate_password_hash`).
- Log in, log out, and stay logged in across pages with Flask sessions.
- Every route except register/login is protected by a `login_required` decorator.

## Book Suggestions
- Any logged-in member can suggest a book by entering a title, author, and a short description.
- All suggestions are listed on `/books` along with the name of the member who suggested them.
- Members can delete their own suggestions, but only if the book is not currently being read.

## Voting
- Each member can vote on any suggested book.
- Votes are toggleable: clicking "Vote / Unvote" adds or removes the member's vote.
- Vote counts are displayed as a badge next to each book, and books are ranked by vote count.

## Discussions
- Every book has its own detail page with a discussion thread.
- Members can post messages and read what others have written.
- Messages are timestamped and attributed to their author.

## Current Reading
- A member can mark a book as "Currently Reading" with a single click.
- Only one book can be "reading" at a time; marking a new one automatically finishes the previous selection.
- When the club finishes the book, anyone can click "Mark as finished" to close the read.
- The dashboard highlights the current book with a prominent card.

## Dashboard
- The home page shows a personalized greeting, the current book, the top five vote-getters, and the five most recent discussion messages.

## Profiles
- Every member has a public profile page showing:
    - Number of books suggested
    - Number of votes cast
    - Number of messages posted
    - Full lists of the above, linked to the relevant books

---

# How to Run
1. Install the dependencies:
    pip install --user -r requirements.txt
2. Start the Flask development server:
    flask run
3. Open the link shown in the terminal in your browser.
    The app will create and use booknest.db in the project folder automatically. On first run, you should register a new account through the web interface and there are no pre-seeded users.

---

# Design Decisions

## Database schema
The app uses a single SQLite database (`booknest.db`) with four tables:

- users — id, username (unique), hash, created_at
- books — id, title, author, description, suggested_by (FK to users), status (`suggested` | `reading` | `finished`), created_at
- votes — id, user_id, book_id, created_at, with a `UNIQUE(user_id, book_id)` constraint to prevent double votes
- discussions — id, book_id, user_id, content, created_at

The `UNIQUE(user_id, book_id)` constraint on `votes` enforces the rule that a member can only vote once per book. When a user clicks "Vote / Unvote", the app checks whether a matching row exists and either deletes it or inserts a new one a toggle pattern that avoids needing a separate boolean flag.

## Only one "currently reading" book
`status = 'reading'` is enforced by doing two updates inside `mark_reading()`: first set every reading book to `finished`, then set the chosen one to `reading`. The dashboard then only shows the current one.

## Session-based auth
Sessions are stored on the filesystem via `flask-session`, not signed cookies. This is the standard CS50 pattern and avoids bloating cookies with user data.

## Why delete cascades manually
SQLite does not enforce foreign keys by default. When a user deletes a book, the app deletes its votes and discussions first, then the book itself. This avoids orphaned rows without needing to enable `PRAGMA foreign_keys = ON`.

## Design and branding
The visual theme uses a forest-green and warm-cream palette that matches the BookNest logo, a stack of books in a nest. CSS variables in `styles.css` centralize the color palette so the theme is easy to change.

---

# Files

- `app.py` — Flask routes and SQL queries
- `helpers.py` — `apology()` and `login_required()` helpers (adapted from CS50's Finance distribution)
- `booknest.db` — SQLite database
- `requirements.txt` — Python dependencies
- `templates/` — Jinja templates
- `layout.html`, `index.html`, `login.html`, `register.html`,
 `suggest.html`, `books.html`, `book.html`, `profile.html`,
 `apology.html`
- `static/styles.css` — Custom theme
- `static/booknested.png` — BookNest logo

---

# Future Improvements
- Reading progress: let the current reader log pages read and show a progress bar on the dashboard.
- Meeting scheduler: pick a date/time/location for the next club meeting and let members respond.
- Book covers: fetch cover art from the Google Books API by ISBN.
- Notifications: email or in-app alerts when a new book is suggested or the current read changes.

## Acknowledgements

The initial structure of this project was inspired by CS50x's Finance problem set, particularly the session/auth pattern in `helpers.py` and `app.py`. All other code the schema, the routes for suggesting, voting, discussing, marking as reading deleting, and the profile page was written for this project.

AI tools used: I used DeepSeek as a coding assistant to help debug python and flask errors and review my SQL schema for consistency. Every line was typed and understood by me, and all design decisions were made by me.

---

© 2026 Josua Cajes
