# 📚 Digital Library Management System

A web-based **Digital Library Management System** developed using Python, Flask, SQLite, HTML, and CSS. This project helps manage books, library members, and book issue/return transactions through a simple and user-friendly interface.

## 🎯 Project Objective

The main objective of this project is to digitize basic library operations, reduce manual record-keeping, and make book and member management easier.

## ✨ Features

- 🔐 Admin login system
- 📊 Dashboard for library overview
- 📚 Add, view, edit, and search books
- 👥 Register and manage library members
- 📖 Issue books to members
- ↩️ Record book returns
- 🔍 Search and manage library records
- 🗄️ SQLite database for data storage
- 🎨 Simple and responsive web interface

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| SQLite | Database management |
| HTML | Web page structure |
| CSS | Styling and layout |
| Git & GitHub | Version control and source code hosting |

## 📂 Project Structure

```text
digital-library-management-system/
│
├── app.py
├── digital_library.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── books.html
│   ├── book_form.html
│   ├── members.html
│   └── transactions.html
│
└── static/
    └── style.css
```

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/chiragbhardwaj295-bit/digital-library-management-system.git
```

### 2. Open the Project Folder

```bash
cd digital-library-management-system
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

### 5. Open in Browser

Visit:

`http://127.0.0.1:5000`

## 🔑 Demo Login

- **Username:** `admin`
- **Password:** `admin123`

Change the default credentials and secret key before using the application beyond a classroom demonstration.

## 🗄️ Database

The application uses SQLite to store library data. The database is initialized by the application when it starts.

**Note:** The SQLite database file is excluded from the public repository to avoid sharing private or personal records.

## 🚀 Deployment

The application can be deployed using a Python-compatible hosting service such as Render. A public deployment URL will be added here after deployment is completed.

**Live Demo:** Not deployed yet.

## 🎓 Academic Project

- **Project Title:** Digital Library Management System
- **Project Type:** College / Academic Project
- **Programming Language:** Python
- **Framework:** Flask
- **Database:** SQLite

## 🔮 Future Enhancements

- Student login and registration
- Book availability notifications
- Book issue due dates and fine calculation
- Exportable library reports
- Improved authentication and role-based access
- Persistent database hosting for online deployment

## 👨‍💻 Author

**Chirag Bhardwaj**

GitHub: [@chiragbhardwaj295-bit](https://github.com/chiragbhardwaj295-bit)

---

⭐ If you find this project useful, consider starring the repository.
