# Digital Library Management System

A beginner-friendly college project built with Python, Flask, SQLite, HTML and CSS.

## Features
- Admin login
- Dashboard with book/member/issue statistics
- Add, edit, delete and search books
- Register and search members
- Issue books and mark books returned
- SQLite database persists between runs

## Run in GitHub Codespaces
Open the terminal in this project folder and run:

```bash
python -m pip install -r requirements.txt
python app.py
```

When Codespaces asks to open port 5000, choose **Open in Browser** (port visibility can be Private).

## Demo login
- Username: `admin`
- Password: `admin123`

Change the demo credentials and `SECRET_KEY` before any real/public deployment. This is a learning project, not production-ready software.

## Database
`library.db` is created automatically on the first run. Do not commit a real database containing personal member data to a public repository.
