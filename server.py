#!/usr/bin/env python3
import html
import json
import re
import unicodedata
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
BLOG_DIR = ROOT / "blogs"
SOURCE_DIR = BLOG_DIR / "source"
PAGES_DIR = BLOG_DIR / "pages"
POSTS_FILE = BLOG_DIR / "posts.json"
POSTS_SCRIPT = BLOG_DIR / "posts-data.js"


def slugify(title):
    value = unicodedata.normalize("NFKC", title).strip().lower()
    value = re.sub(r"[^\w\u4e00-\u9fff]+", "-", value, flags=re.UNICODE).strip("-")
    return value[:60] or f"post-{date.today().isoformat()}"


def inline_markdown(line):
    line = html.escape(line)
    line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", line)


def render_markdown(source):
    blocks, paragraph, code_lines, list_items = [], [], [], []
    in_code = False

    def flush():
        if paragraph:
            blocks.append(f"<p>{'<br />'.join(paragraph)}</p>")
            paragraph.clear()

    def flush_list():
        if list_items:
            blocks.append("<ul>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ul>")
            list_items.clear()

    for raw_line in source.splitlines():
        if raw_line.strip().startswith("```"):
            if in_code:
                blocks.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
            else:
                flush(); flush_list()
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(raw_line)
            continue
        line = inline_markdown(raw_line)
        if not line.strip():
            flush(); flush_list()
        elif line.startswith("### "):
            flush(); flush_list(); blocks.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            flush(); flush_list(); blocks.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            flush(); flush_list(); blocks.append(f"<h2>{line[2:]}</h2>")
        elif line.startswith("&gt; "):
            flush(); flush_list(); blocks.append(f"<blockquote>{line[5:]}</blockquote>")
        elif line.startswith("- "):
            flush(); list_items.append(line[2:])
        else:
            flush_list()
            paragraph.append(line)
    if code_lines:
        blocks.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    flush(); flush_list()
    return "\n".join(blocks)


def markdown_document(post):
    return "\n".join([
        "---",
        f"title: {json.dumps(post['title'], ensure_ascii=False)}",
        f"category: {json.dumps(post['category'], ensure_ascii=False)}",
        f"date: {post['date']}",
        f"slug: {post['slug']}",
        "---",
        "",
        post["content"],
        "",
    ])


def read_markdown(path):
    text = path.read_text("utf-8")
    match = re.match(r"^---\n(.*?)\n---\n?", text, re.DOTALL)
    if not match:
        raise ValueError("Markdown 文件缺少元数据")
    metadata = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        value = value.strip()
        try:
            metadata[key.strip()] = json.loads(value)
        except json.JSONDecodeError:
            metadata[key.strip()] = value
    metadata["content"] = text[match.end():].strip()
    return metadata


def legacy_html_to_markdown(source):
    match = re.search(r'<div class="post-content">(.*?)</div></article>', source, re.DOTALL)
    body = match.group(1) if match else source
    replacements = [
        (r"<h2>(.*?)</h2>", r"\n## \1\n"),
        (r"<h3>(.*?)</h3>", r"\n### \1\n"),
        (r"<blockquote>(.*?)</blockquote>", r"\n> \1\n"),
        (r"<strong>(.*?)</strong>", r"**\1**"),
        (r"<code>(.*?)</code>", r"`\1`"),
        (r"<br\s*/?>", "\n"),
        (r"</p>\s*<p>", "\n\n"),
        (r"</?p>", ""),
    ]
    for pattern, replacement in replacements:
        body = re.sub(pattern, replacement, body, flags=re.DOTALL | re.IGNORECASE)
    return html.unescape(re.sub(r"<[^>]+>", "", body)).strip()


def migrate_legacy_posts():
    if not POSTS_FILE.exists():
        return
    posts = json.loads(POSTS_FILE.read_text("utf-8"))
    changed = False
    migrated = []
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    for item in posts:
        if item.get("slug") and item.get("source"):
            migrated.append(item)
            continue
        slug = slugify(item["title"])
        legacy_path = ROOT / item["url"]
        content = legacy_html_to_markdown(legacy_path.read_text("utf-8")) if legacy_path.exists() else ""
        post = {**item, "slug": slug, "content": content,
                "source": f"blogs/source/{slug}.md", "url": f"blogs/pages/{slug}.html"}
        (SOURCE_DIR / f"{slug}.md").write_text(markdown_document(post), "utf-8")
        (PAGES_DIR / f"{slug}.html").write_text(post_page(post), "utf-8")
        migrated.append({key: post[key] for key in ("slug", "title", "category", "date", "source", "url")})
        changed = True
    if changed:
        write_posts(migrated)


def post_page(post):
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{html.escape(post['title'])}｜Yu Li</title><link rel="stylesheet" href="../../styles.css" /></head>
<body class="post-page"><main class="post-shell">
<div class="post-toolbar"><a class="post-back" href="../../index.html#notes">← 返回博客</a><a class="post-edit" data-editor-access href="../../blog-editor.html?edit={post['slug']}" hidden>编辑文章 ↗</a></div>
<article><h1>{html.escape(post['title'])}</h1><div class="post-content">{render_markdown(post['content'])}</div></article>
</main><aside class="post-toc" aria-label="文章目录"><p>本文目录</p><nav id="post-toc-list"></nav></aside><script src="../../post-toc.js"></script><script src="../../editor-access.js"></script></body></html>'''


def write_posts(posts):
    payload = json.dumps(posts, ensure_ascii=False, indent=2)
    POSTS_FILE.write_text(payload, "utf-8")
    POSTS_SCRIPT.write_text(f"window.BLOG_POSTS = {payload};\n", "utf-8")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/api/posts/"):
            try:
                slug = unquote(path.removeprefix("/api/posts/"))
                if not re.fullmatch(r"[\w\u4e00-\u9fff-]+", slug):
                    raise ValueError("无效的文章标识")
                source = SOURCE_DIR / f"{slug}.md"
                if not source.exists():
                    self.respond(404, {"error": "找不到文章原文"})
                    return
                self.respond(200, read_markdown(source))
            except (ValueError, OSError) as error:
                self.respond(400, {"error": str(error)})
            return
        if path.startswith("/blogs/") and path.endswith(".html") and "/pages/" not in path:
            posts = json.loads(POSTS_FILE.read_text("utf-8")) if POSTS_FILE.exists() else []
            if len(posts) == 1:
                self.send_response(302)
                self.send_header("Location", "/" + posts[0]["url"])
                self.end_headers()
                return
        super().do_GET()

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

            SOURCE_DIR.mkdir(parents=True, exist_ok=True)
            PAGES_DIR.mkdir(parents=True, exist_ok=True)
            posts = json.loads(POSTS_FILE.read_text("utf-8")) if POSTS_FILE.exists() else []
            requested_slug = str(data.get("slug") or "").strip()
            slug = requested_slug if re.fullmatch(r"[\w\u4e00-\u9fff-]+", requested_slug) else slugify(title)
            post = {
                "slug": slug,
                "title": title,
                "category": str(data.get("category") or "未分类")[:50],
                "date": str(data.get("date") or date.today().isoformat())[:10],
                "content": content,
                "source": f"blogs/source/{slug}.md",
                "url": f"blogs/pages/{slug}.html",
            }
            (SOURCE_DIR / f"{slug}.md").write_text(markdown_document(post), "utf-8")
            (PAGES_DIR / f"{slug}.html").write_text(post_page(post), "utf-8")
            posts = [item for item in posts if item.get("slug") != slug and item.get("title") != title]
            posts.insert(0, {key: post[key] for key in ("slug", "title", "category", "date", "source", "url")})
            write_posts(posts)
            self.respond(201, {"url": "/" + post["url"]})
        except (ValueError, json.JSONDecodeError) as error:
            self.respond(400, {"error": str(error)})
        except OSError as error:
            self.respond(500, {"error": f"写入文件失败：{error}"})

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def respond(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    migrate_legacy_posts()
    print("博客已启动：http://localhost:4173")
    ThreadingHTTPServer(("127.0.0.1", 4173), Handler).serve_forever()
