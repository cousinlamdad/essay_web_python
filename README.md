# Essay Web

A simple essay management web app built with **Python**, **Flask**, **Jinja2**, **i18n**, and **MariaDB**.

## Features

- **Input Essay** — save an essay to MariaDB
- **Essay List** — view all saved essays
- **Essay Detail** — click an essay to display it
- **i18n** — switch between English and Chinese (中文)

## Tech Stack

- Backend: Python + Flask + PyMySQL + Jinja2 templates
- Frontend: server-rendered HTML + CSS (no JavaScript build step)
- Database: MariaDB
- Production server: Waitress

## Project Structure

```
essay_web/
├── app.py                 # Flask application (pages + JSON API)
├── requirements.txt       # Python dependencies
├── locales/
│   ├── en.json            # English translations
│   └── zh.json            # Chinese translations
├── templates/
│   ├── base.html          # Layout (header, nav, language toggle)
│   ├── input_essay.html   # Upload form
│   ├── essay_list.html    # Essay list
│   ├── essay_detail.html  # Essay detail
│   └── not_found.html     # 404 page
├── static/
│   ├── style.css
│   ├── favicon.svg
│   └── icons.svg
├── essay_web.sql          # Database schema dump
├── .env.example
└── .env
```

## Prerequisites

- Python (>= 3.10)
- MariaDB running locally (or a reachable MariaDB instance)

## Database Setup

1. Create a database and user:

```sql
CREATE DATABASE IF NOT EXISTS essay_web
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'essay_app'@'localhost'
  IDENTIFIED BY 'your_app_password';

GRANT ALL PRIVILEGES ON essay_web.* TO 'essay_app'@'localhost';
FLUSH PRIVILEGES;
```

2. Create the `essays` table:

```sql
CREATE TABLE IF NOT EXISTS essays (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  content TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

(Or import `essay_web.sql`.)

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
PORT=3012
DB_HOST=localhost
DB_PORT=3306
DB_USER=essay_app
DB_PASSWORD=your_app_password
DB_NAME=essay_web
```

> `.env` is git-ignored and should never be committed.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Then open: http://localhost:3012

The app serves the rendered pages and the JSON API from the same port. It uses
Waitress when installed, and falls back to the Flask development server otherwise.

## API Endpoints

| Method | Path              | Description               |
| ------ | ----------------- | ------------------------- |
| POST   | `/api/essays`     | Create a new essay        |
| GET    | `/api/essays`     | List all essays           |
| GET    | `/api/essays/:id` | Get one essay by ID       |

### Request body (POST)

```json
{
  "title": "My Essay",
  "content": "Essay body..."
}
```

## i18n

Translations are defined in `locales/`. Use the button in the top navigation to
toggle between English and Chinese. The choice is stored in a `lang` cookie.

To add another language, create `locales/<lang>.json` and register its code in
`app.py` where `TRANSLATIONS` is loaded.
