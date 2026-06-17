from os import getenv
import re
import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from time import time

from flask import Flask, Response, request
from jinja2 import BaseLoader, Environment, select_autoescape
from markupsafe import escape
from werkzeug.serving import WSGIRequestHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH'] = 4096

WSGIRequestHandler.server_version = 'Secure Flask Demo'
WSGIRequestHandler.sys_version = ''

MAX_NAME_LENGTH = 40
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,'-]*$")

template_env = Environment(loader=BaseLoader(), autoescape=select_autoescape(["html", "xml"]))
STYLES_LAST_MODIFIED = datetime(2026, 6, 17, 0, 0, 0, tzinfo=timezone.utc)

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fancy Greeting</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <div class="glow one"></div>
    <div class="glow two"></div>

    <main class="card">
        <span class="badge">Advanced Prompts · Secure Flask Demo</span>
        <h1><span class="accent">Hello, {{ name }}!</span></h1>
        <p>
            A polished greeting page with safer input handling, a length limit, and a UI that is a little more
            lively than plain text.
        </p>

        <form method="post" action="/">
            <label for="name">Customize the greeting</label>
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <div class="field-row">
                <input
                    id="name"
                    name="name"
                    type="text"
                    maxlength="{{ max_length }}"
                    placeholder="Type your name"
                    autocomplete="name"
                >
                <button type="submit">Refresh</button>
            </div>
        </form>

        <section class="preview" aria-live="polite">
            <strong>Preview</strong>
            <span>{{ preview_message }}</span>
        </section>

        <div class="meta">
            <span class="chip">Trimmed input</span>
            <span class="chip">Length capped at {{ max_length }} chars</span>
            <span class="chip">Escaped output</span>
            <span class="chip">No unsafe HTML injection</span>
        </div>
    </main>
</body>
</html>
"""

STYLE_CSS = """
:root {
    color-scheme: dark;
    --bg: #08111f;
    --bg-2: #101a33;
    --card: rgba(14, 23, 44, 0.78);
    --card-border: rgba(255, 255, 255, 0.15);
    --text: #f4f7ff;
    --muted: #b7c2e0;
    --accent: #7c5cff;
    --accent-2: #2dd4bf;
    --accent-3: #ff7a59;
    --shadow: 0 24px 80px rgba(0, 0, 0, 0.45);
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    color: var(--text);
    background:
        radial-gradient(circle at top left, rgba(124, 92, 255, 0.35), transparent 28%),
        radial-gradient(circle at top right, rgba(45, 212, 191, 0.25), transparent 22%),
        radial-gradient(circle at bottom center, rgba(255, 122, 89, 0.16), transparent 24%),
        linear-gradient(160deg, var(--bg), var(--bg-2));
    display: grid;
    place-items: center;
    overflow: hidden;
}

.glow {
    position: fixed;
    inset: auto;
    width: 28rem;
    height: 28rem;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.34;
    pointer-events: none;
    animation: drift 12s ease-in-out infinite alternate;
}

.glow.one {
    top: -8rem;
    left: -6rem;
    background: rgba(124, 92, 255, 0.55);
}

.glow.two {
    right: -7rem;
    bottom: -8rem;
    background: rgba(45, 212, 191, 0.42);
    animation-delay: -4s;
}

.card {
    width: min(92vw, 760px);
    position: relative;
    padding: clamp(1.5rem, 4vw, 3rem);
    border: 1px solid var(--card-border);
    border-radius: 28px;
    background: linear-gradient(180deg, rgba(18, 28, 53, 0.88), rgba(9, 16, 31, 0.88));
    box-shadow: var(--shadow);
    backdrop-filter: blur(22px);
    animation: rise 0.8s ease-out both;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.55rem 0.9rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: var(--muted);
    font-size: 0.92rem;
    letter-spacing: 0.02em;
}

h1 {
    margin: 1rem 0 0.4rem;
    font-size: clamp(2.4rem, 6vw, 4.75rem);
    line-height: 0.98;
    letter-spacing: -0.05em;
}

.accent {
    background: linear-gradient(90deg, var(--accent), var(--accent-2), var(--accent-3));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

p {
    margin: 0.85rem 0 0;
    color: var(--muted);
    font-size: 1.05rem;
    line-height: 1.6;
    max-width: 56ch;
}

form {
    margin-top: 1.75rem;
    display: grid;
    gap: 0.9rem;
}

label {
    font-size: 0.95rem;
    color: var(--muted);
}

.field-row {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
}

input {
    flex: 1 1 280px;
    min-width: 0;
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 16px;
    padding: 0.95rem 1rem;
    background: rgba(8, 14, 27, 0.88);
    color: var(--text);
    font-size: 1rem;
    outline: none;
    transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

input:focus {
    border-color: rgba(124, 92, 255, 0.9);
    box-shadow: 0 0 0 4px rgba(124, 92, 255, 0.16);
    transform: translateY(-1px);
}

button {
    border: 0;
    border-radius: 16px;
    padding: 0.95rem 1.2rem;
    font-weight: 700;
    color: white;
    background: linear-gradient(135deg, var(--accent), var(--accent-3));
    cursor: pointer;
    box-shadow: 0 14px 30px rgba(124, 92, 255, 0.26);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 18px 36px rgba(124, 92, 255, 0.34);
}

.preview {
    margin-top: 1.5rem;
    padding: 1rem 1.1rem;
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.05);
}

.preview strong {
    display: block;
    margin-bottom: 0.35rem;
}

.meta {
    margin-top: 1.25rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.7rem;
}

.chip {
    padding: 0.5rem 0.8rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: var(--muted);
    font-size: 0.88rem;
}

@keyframes drift {
    from {
        transform: translate3d(0, 0, 0) scale(1);
    }
    to {
        transform: translate3d(1.5rem, 1rem, 0) scale(1.08);
    }
}

@keyframes rise {
    from {
        opacity: 0;
        transform: translateY(20px) scale(0.98);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

@media (max-width: 640px) {
    body {
        padding: 1rem;
    }

    .card {
        border-radius: 22px;
    }

    .field-row {
        flex-direction: column;
    }

    button {
        width: 100%;
    }
}
"""

ERROR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Request Error</title>
    <style>
        body {
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            color: #f4f7ff;
            background: linear-gradient(160deg, #08111f, #101a33);
        }

        .panel {
            width: min(92vw, 560px);
            padding: 2rem;
            border-radius: 24px;
            background: rgba(18, 28, 53, 0.88);
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 24px 80px rgba(0, 0, 0, 0.45);
        }

        h1 {
            margin: 0 0 0.75rem;
            font-size: 2rem;
        }

        p {
            margin: 0;
            color: #b7c2e0;
            line-height: 1.6;
        }

        a {
            display: inline-block;
            margin-top: 1.25rem;
            color: #7c5cff;
            text-decoration: none;
            font-weight: 700;
        }
    </style>
</head>
<body>
    <main class="panel">
        <h1>{{ title }}</h1>
        <p>{{ message }}</p>
        <a href="/">Back to home</a>
    </main>
</body>
</html>
"""


def normalize_name(raw_name: str | None) -> str:
    """Return a safe, display-friendly name."""
    if raw_name is None:
        return 'World'

    name = raw_name.strip()
    if not name:
        return 'World'

    if len(name) > MAX_NAME_LENGTH:
        raise ValueError('Name is too long')

    if not NAME_PATTERN.fullmatch(name):
        raise ValueError('Name contains unsupported characters')

    return name


def render_page(template: str, **context: str) -> str:
    return template_env.from_string(template).render(**context)


def get_csrf_token() -> str:
    timestamp = str(int(time()))
    nonce = secrets.token_urlsafe(16)
    payload = f'{timestamp}:{nonce}'
    signature = hmac.new(app.config['SECRET_KEY'].encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    return f'{payload}:{signature}'


def validate_csrf_token(form_token: str | None) -> None:
    if not form_token:
        raise ValueError('Invalid CSRF token')

    parts = form_token.split(':', 2)
    if len(parts) != 3:
        raise ValueError('Invalid CSRF token')

    timestamp, nonce, signature = parts
    payload = f'{timestamp}:{nonce}'
    expected_signature = hmac.new(
        app.config['SECRET_KEY'].encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError('Invalid CSRF token')

    if not timestamp.isdigit() or int(time()) - int(timestamp) > 300:
        raise ValueError('Invalid CSRF token')


@app.after_request
def add_security_headers(response: Response) -> Response:
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    if response.mimetype == 'text/css':
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    else:
        response.headers['Cache-Control'] = 'public, max-age=600'
    response.headers['Content-Security-Policy'] = (
        "default-src 'none'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "script-src 'none'; "
        "connect-src 'none'; "
        "object-src 'none'; "
        "frame-src 'none'; "
        "base-uri 'none'; "
        "form-action 'self'; "
        "frame-ancestors 'none';"
    )
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=(), usb=()'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
    return response


@app.route('/', methods=['GET', 'POST'])
def hello():
    csrf_token = get_csrf_token()
    raw_name = request.form.get('name') if request.method == 'POST' else None

    try:
        if request.method == 'POST':
            validate_csrf_token(request.form.get('csrf_token'))
        name = normalize_name(raw_name)
    except ValueError as error:
        return bad_request(error)

    if request.method == 'POST':
        csrf_token = get_csrf_token()

    preview_message = f'Hello, {name}! This page is designed to be colorful, readable, and safe.'

    page = render_page(
        PAGE_TEMPLATE,
        name=escape(name),
        preview_message=escape(preview_message),
        max_length=MAX_NAME_LENGTH,
        csrf_token=escape(csrf_token),
    )

    return Response(page, mimetype='text/html; charset=utf-8')


@app.route('/robots.txt')
def robots_txt():
    return Response('User-agent: *\nDisallow: /\n', mimetype='text/plain; charset=utf-8')


@app.route('/sitemap.xml')
def sitemap_xml():
    page = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
  <url>
    <loc>/</loc>
  </url>
</urlset>
"""
    return Response(page, mimetype='application/xml; charset=utf-8')


@app.route('/styles.css')
def styles_css():
    response = Response(STYLE_CSS, mimetype='text/css; charset=utf-8')
    response.set_etag('styles-v1')
    response.last_modified = STYLES_LAST_MODIFIED
    response.make_conditional(request)
    return response


@app.errorhandler(400)
def bad_request(error):
    message = 'Invalid input. Use letters, numbers, spaces, apostrophes, periods, commas, and hyphens only.'
    page = render_page(ERROR_TEMPLATE, title='Bad Request', message=message)
    return Response(page, status=400, mimetype='text/html; charset=utf-8')


@app.errorhandler(500)
def internal_error(error):
    page = render_page(
        ERROR_TEMPLATE,
        title='Server Error',
        message='Something went wrong on the server. Please try again later.',
    )
    return Response(page, status=500, mimetype='text/html; charset=utf-8')


if __name__ == '__main__':
    debug_mode = getenv('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes', 'on'}
    host = getenv('FLASK_HOST', '127.0.0.1')
    port = int(getenv('FLASK_PORT', '5000'))
    app.run(host=host, port=port, debug=debug_mode)