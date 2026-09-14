import json
import os
import sys
from pathlib import Path

import pymysql
import pymysql.cursors
from dotenv import load_dotenv
from flask import (
    Flask,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER", "essay_app"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "essay_web"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}

DEFAULT_LANG = "en"


def _flatten(data, prefix=""):
    out = {}
    for key, value in data.items():
        full_key = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(_flatten(value, full_key + "."))
        else:
            out[full_key] = value
    return out


TRANSLATIONS = {}
for _code in ("en", "zh"):
    with open(BASE_DIR / "locales" / f"{_code}.json", encoding="utf-8") as f:
        TRANSLATIONS[_code] = _flatten(json.load(f))


def get_locale():
    lang = request.cookies.get("lang", DEFAULT_LANG)
    return lang if lang in TRANSLATIONS else DEFAULT_LANG


def translate(key, lang=None):
    lang = lang or get_locale()
    return TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS[DEFAULT_LANG].get(key, key)


@app.context_processor
def inject_i18n():
    return {"lang": get_locale(), "t": translate}


def get_db():
    if "db" not in g:
        g.db = pymysql.connect(**DB_CONFIG)
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/<path:filename>")
def public_file(filename):
    if filename in ("favicon.svg", "icons.svg"):
        return send_from_directory(app.static_folder, filename)
    return render_template("not_found.html"), 404


# ---------- Pages ----------

@app.route("/", methods=["GET", "POST"])
def input_essay():
    status = None
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        content = request.form.get("content")
        if not title:
            status = translate("input.error")
        else:
            db = get_db()
            with db.cursor() as cur:
                cur.execute(
                    "INSERT INTO essays (title, content) VALUES (%s, %s)",
                    (title, content),
                )
            status = translate("input.saved")
    return render_template("input_essay.html", status=status)


@app.route("/essays")
def essay_list():
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT id, title, created_at FROM essays ORDER BY created_at DESC"
        )
        essays = cur.fetchall()
    return render_template("essay_list.html", essays=essays)


@app.route("/essays/<int:essay_id>")
def essay_detail(essay_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT id, title, content, created_at FROM essays WHERE id = %s",
            (essay_id,),
        )
        essay = cur.fetchone()
    if essay is None:
        return render_template("not_found.html"), 404
    return render_template("essay_detail.html", essay=essay)


@app.route("/language/<lang>")
def set_language(lang):
    next_url = request.args.get("next") or url_for("input_essay")
    if not next_url.startswith("/"):
        next_url = url_for("input_essay")
    resp = redirect(next_url)
    if lang in TRANSLATIONS:
        resp.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365)
    return resp


# ---------- JSON API ----------

def _serialize(essay):
    return {
        **essay,
        "created_at": essay["created_at"].isoformat()
        if essay.get("created_at")
        else None,
    }


@app.get("/api/essays")
def api_list_essays():
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT id, title, created_at FROM essays ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
    return jsonify([_serialize(row) for row in rows])


@app.get("/api/essays/<int:essay_id>")
def api_get_essay(essay_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT id, title, content, created_at FROM essays WHERE id = %s",
            (essay_id,),
        )
        essay = cur.fetchone()
    if essay is None:
        return jsonify({"error": "Essay not found"}), 404
    return jsonify(_serialize(essay))


@app.post("/api/essays")
def api_create_essay():
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    if not title or not isinstance(title, str):
        return jsonify({"error": "Title is required"}), 400
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO essays (title, content) VALUES (%s, %s)",
            (title, data.get("content")),
        )
    return jsonify({"id": cur.lastrowid}), 201


@app.errorhandler(500)
def internal_error(err):
    app.logger.exception("Internal server error: %s", err)
    if request.path.startswith("/api"):
        return jsonify({"error": "Internal server error"}), 500
    return "Internal server error", 500


if __name__ == "__main__":
    try:
        conn = pymysql.connect(**DB_CONFIG)
        conn.close()
    except Exception as err:
        print(f"Failed to connect to MariaDB: {err}", file=sys.stderr)
        sys.exit(1)

    port = int(os.environ.get("PORT", 3001))
    print(f"Server listening on http://localhost:{port}")
    try:
        from waitress import serve

        serve(app, host="0.0.0.0", port=port)
    except ImportError:
        app.run(host="0.0.0.0", port=port)
