#!/usr/bin/env python3
import html
import json
import re
import unicodedata
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
BLOG_DIR = ROOT / "blogs"
POSTS_FILE = BLOG_DIR / "posts.json"


def slugify(title):
    value = unicodedata.normalize("NFKC", title).strip().lower()
    value = re.sub(r"[^\w\u4e00-\u9fff]+", "-", value, flags=re.UNICODE).strip("-")
    return value[:60] or f"post-{date.today().isoformat()}"


def render_markdown(source):
    blocks, paragraph = [], []

    def flush():
        if paragraph:
            blocks.append(f"<p>{'<br />'.join(paragraph)}</p>")
            paragraph.clear()

    for raw_line in source.splitlines():
        line = html.escape(raw_line)
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        line = re.sub(r"`(.+?)`", r"<code>\1</code>", line)
        if not line.strip():
            flush()
        elif line.startswith("### "):
            flush(); blocks.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            flush(); blocks.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            flush(); blocks.append(f"<h2>{line[2:]}</h2>")
        else:
            paragraph.append(line)
    flush()
    return "\n".join(blocks)


def post_page(post):
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{html.escape(post['title'])}｜Yu Li</title><link rel="stylesheet" href="../styles.css" /></head>
<body class="post-page"><main class="post-shell">
<a class="post-back" href="../index.html#notes">← 返回博客</a>
<article><div class="post-meta"><span>{html.escape(post['category'])}</span><time>{html.escape(post['date'])}</time></div>
<h1>{html.escape(post['title'])}</h1><div class="post-content">{render_markdown(post['content'])}</div></article>
</main></body></html>'''


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_POST(self):
        if urlparse(self.path).path != "/api/posts":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 2_000_000:
                raise ValueError("文章内容过大")
            data = json.loads(self.rfile.read(length))
            title = str(data.get("title", "")).strip()
            content = str(data.get("content", "")).strip()
            if not title or not content:
                raise ValueError("标题和正文不能为空")

            BLOG_DIR.mkdir(exist_ok=True)
            posts = json.loads(POSTS_FILE.read_text("utf-8")) if POSTS_FILE.exists() else []
            base, slug, number = slugify(title), slugify(title), 2
            while (BLOG_DIR / f"{slug}.html").exists():
                slug = f"{base}-{number}"; number += 1
            post = {
                "title": title,
                "category": str(data.get("category") or "未分类")[:50],
                "date": str(data.get("date") or date.today().isoformat())[:10],
                "content": content,
                "url": f"blogs/{slug}.html",
            }
            (BLOG_DIR / f"{slug}.html").write_text(post_page(post), "utf-8")
            posts.insert(0, {key: post[key] for key in ("title", "category", "date", "url")})
            POSTS_FILE.write_text(json.dumps(posts, ensure_ascii=False, indent=2), "utf-8")
            self.respond(201, {"url": post["url"]})
        except (ValueError, json.JSONDecodeError) as error:
            self.respond(400, {"error": str(error)})
        except OSError as error:
            self.respond(500, {"error": f"写入文件失败：{error}"})

    def respond(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print("博客已启动：http://localhost:4173")
    ThreadingHTTPServer(("127.0.0.1", 4173), Handler).serve_forever()
