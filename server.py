#!/usr/bin/env python3
"""
Local server for the News Reader.
Run: python server.py
Then open http://localhost:5000 in your browser.
"""

import urllib.parse
import sys
import os

try:
    from flask import Flask, request, jsonify, send_from_directory
except ImportError:
    sys.exit(
        "Install dependencies:\n"
        "  pip install flask requests trafilatura newspaper3k beautifulsoup4 lxml"
    )

try:
    import requests as req
except ImportError:
    sys.exit("Install: pip install requests")

try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

try:
    from newspaper import Article
    HAS_NEWSPAPER = True
except ImportError:
    HAS_NEWSPAPER = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
    "DNT": "1",
}

SESSION = req.Session()
SESSION.headers.update(HEADERS)
TIMEOUT = 15


def _get(url):
    try:
        r = SESSION.get(url, timeout=TIMEOUT, allow_redirects=True)
        r.raise_for_status()
        return r
    except Exception:
        return None


def extract_text(html, url=""):
    if HAS_TRAFILATURA:
        t = trafilatura.extract(html, include_comments=False, include_tables=False)
        if t and len(t) > 200:
            return t
    if HAS_BS4:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup.select(
            "script,style,nav,header,footer,aside,"
            "[class*='paywall'],[class*='subscribe'],[id*='paywall'],"
            "[class*='overlay'],[class*='modal'],[class*='signup']"
        ):
            tag.decompose()
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        text = "\n\n".join(p for p in paragraphs if len(p) > 40)
        if text and len(text) > 200:
            return text
    return None


def get_page_title(html):
    if HAS_BS4:
        soup = BeautifulSoup(html, "lxml")
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            return og["content"].strip()
        if soup.title:
            return soup.title.string.strip()
    return None


def get_page_image(html):
    if HAS_BS4:
        soup = BeautifulSoup(html, "lxml")
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"].strip()
    return None


def method_direct(url):
    r = _get(url)
    if not r:
        return None, None, None
    return get_page_title(r.text), extract_text(r.text, url), get_page_image(r.text)


def method_newspaper(url):
    if not HAS_NEWSPAPER:
        return None, None, None
    try:
        art = Article(url, language="en")
        art.download()
        art.parse()
        if art.text and len(art.text) > 200:
            return art.title or None, art.text, art.top_image or None
    except Exception:
        pass
    return None, None, None


def method_wayback(url):
    api = f"https://archive.org/wayback/available?url={urllib.parse.quote(url)}"
    r = _get(api)
    if not r:
        return None, None, None
    snapshot = r.json().get("archived_snapshots", {}).get("closest", {})
    if not snapshot.get("available"):
        return None, None, None
    r2 = _get(snapshot["url"])
    if not r2:
        return None, None, None
    return get_page_title(r2.text), extract_text(r2.text, url), get_page_image(r2.text)


def method_google_cache(url):
    cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{urllib.parse.quote(url)}"
    r = _get(cache_url)
    if not r:
        return None, None, None
    return get_page_title(r.text), extract_text(r.text, url), get_page_image(r.text)


def method_12ft(url):
    proxy_url = f"https://12ft.io/proxy?q={urllib.parse.quote(url)}"
    r = _get(proxy_url)
    if not r:
        return None, None, None
    return get_page_title(r.text), extract_text(r.text, url), get_page_image(r.text)


METHODS = [
    ("Direct access", method_direct),
    ("newspaper3k", method_newspaper),
    ("Wayback Machine", method_wayback),
    ("Google Cache", method_google_cache),
    ("12ft.io", method_12ft),
]


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/read", methods=["POST"])
def read():
    data = request.get_json()
    url = (data or {}).get("url", "").strip()
    if not url:
        return jsonify({"error": "URL not provided"}), 400
    if not url.startswith("http"):
        url = "https://" + url

    for name, method_fn in METHODS:
        title, text, image = method_fn(url)
        if text and len(text) > 200:
            return jsonify({
                "title": title or "Untitled",
                "text": text,
                "image": image,
                "method": name,
            })

    return jsonify({"error": "Could not extract content by any method."}), 422


@app.route("/ping")
def ping():
    return "ok"


if __name__ == "__main__":
    print("\n  News Reader — local server")
    print("  ─────────────────────────────────────")
    print("  Open in browser: http://localhost:5000")
    print("  Press Ctrl+C to stop.\n")
    app.run(port=5000, debug=False)
