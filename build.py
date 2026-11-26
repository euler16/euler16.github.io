#!/usr/bin/env python3
"""
Static site builder for mehedieh.github.io.

    python build.py            # build into _site/
    python build.py --serve    # build, then serve _site on http://localhost:8000

Content lives in content/ (site.yml, posts/*.md, projects/*.md), layouts in
templates/, and static assets in static/. Output is plain HTML with one
directory per page, so every route survives a refresh on GitHub Pages.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import math
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image
from pygments.formatters import HtmlFormatter

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUT = ROOT / "_site"

WORDS_PER_MINUTE = 220


# ── Helpers ────────────────────────────────────────────────────────────────

def read_front_matter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


FENCE_RE = re.compile(r"(^(```|~~~)[^\n]*\n.*?^\2[ \t]*$)", re.S | re.M)
DISPLAY_MATH_RE = re.compile(r"\$\$(.+?)\$\$", re.S)
INLINE_MATH_RE = re.compile(r"(?<![\\$])\$(?!\s*\$)([^\n$]+?)(?<!\\)\$")


def protect_math(src: str) -> tuple[str, list[tuple[str, str]]]:
    """Pull TeX out before Markdown sees it (so _ and \\ survive)."""
    store: list[tuple[str, str]] = []

    def keep(kind: str, tex: str) -> str:
        store.append((kind, tex.strip()))
        return f"MATHTOKEN{len(store) - 1}X"

    def process(chunk: str) -> str:
        chunk = DISPLAY_MATH_RE.sub(lambda m: "\n\n" + keep("display", m.group(1)) + "\n\n", chunk)
        return INLINE_MATH_RE.sub(lambda m: keep("inline", m.group(1)), chunk)

    out, last = [], 0
    for m in FENCE_RE.finditer(src):
        out.append(process(src[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(process(src[last:]))
    return "".join(out), store


def restore_math(rendered: str, store: list[tuple[str, str]]) -> str:
    def sub(m: re.Match) -> str:
        kind, tex = store[int(m.group(1))]
        if kind == "display":
            # Numbered environments become unnumbered ones (the originals never showed numbers).
            tex = re.sub(r"\\(begin|end)\{(align|equation|gather)\*?\}",
                         lambda e: f"\\{e.group(1)}{{{ {'align': 'aligned', 'equation': 'split', 'gather': 'gathered'}[e.group(2)] }}}", tex)
            # Bare "\\" line breaks are wrapped so each line renders separately.
            if "\\\\" in tex and "\\begin" not in tex:
                tex = "\\begin{gathered}" + tex + "\\end{gathered}"
            return f'<div class="math-display">\\[{html.escape(tex, quote=False)}\\]</div>'
        return f'<span class="math-inline">\\({html.escape(tex, quote=False)}\\)</span>'

    rendered = re.sub(r"<p>\s*MATHTOKEN(\d+)X\s*</p>", sub, rendered)
    return re.sub(r"MATHTOKEN(\d+)X", sub, rendered)


def normalise_headings(src: str) -> str:
    """Shift headings so the shallowest is h2 (the page title is the h1)."""
    levels = [len(m.group(1)) for m in re.finditer(r"^(#{1,6})\s", FENCE_RE.sub("", src), re.M)]
    if not levels:
        return src
    shift = 2 - min(levels)
    if shift <= 0:
        return src

    def fix(chunk: str) -> str:
        return re.sub(r"^(#{1,6})(\s)", lambda m: "#" * min(6, len(m.group(1)) + shift) + m.group(2), chunk, flags=re.M)

    pieces, last = [], 0
    for m in FENCE_RE.finditer(src):
        pieces.append(fix(src[last:m.start()]))
        pieces.append(m.group(0))
        last = m.end()
    pieces.append(fix(src[last:]))
    return "".join(pieces)


_img_cache: dict[str, tuple[int, int]] = {}


def image_size(url: str) -> tuple[int, int] | None:
    if not url.startswith("/"):
        return None
    if url in _img_cache:
        return _img_cache[url]
    path = STATIC / url.lstrip("/")
    if not path.exists():
        return None
    if path.suffix == ".svg":
        m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', path.read_text(encoding="utf-8"))
        size = (int(float(m.group(1))), int(float(m.group(2)))) if m else None
    else:
        with Image.open(path) as im:
            size = im.size
    _img_cache[url] = size
    return size


def enhance_html(rendered: str) -> str:
    # Images on their own line become figures with intrinsic size (no layout shift).
    def figure(m: re.Match) -> str:
        attrs = m.group(1)
        src = re.search(r'src="([^"]+)"', attrs).group(1)
        size = image_size(src)
        dims = f' width="{size[0]}" height="{size[1]}"' if size else ""
        return f'<figure class="figure"><img{attrs}{dims} loading="lazy" decoding="async"></figure>'

    rendered = re.sub(r"<p>\s*<img([^>]*?)\s*/?>\s*</p>", figure, rendered)
    # External links open safely and are marked for screen readers.
    def ext(m: re.Match) -> str:
        href = m.group(1)
        return f'<a href="{href}" rel="noopener" target="_blank"'

    rendered = re.sub(r'<a href="(https?://[^"]+)"', ext, rendered)
    # Wide tables scroll on small screens.
    rendered = rendered.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    return rendered


def make_markdown() -> markdown.Markdown:
    return markdown.Markdown(
        extensions=["extra", "sane_lists", "smarty", "toc", "codehilite"],
        extension_configs={
            "codehilite": {"css_class": "highlight", "guess_lang": False},
            "toc": {"permalink": "#", "permalink_class": "heading-anchor",
                    "permalink_title": "Link to this section", "toc_depth": "2-3"},
        },
        output_format="html",
    )


def render_markdown(src: str) -> tuple[str, list, bool]:
    src = normalise_headings(src)
    src = re.sub(r"~~(.+?)~~", r"<del>\1</del>", src)
    src, math_store = protect_math(src)
    md = make_markdown()
    rendered = md.convert(src)
    rendered = restore_math(rendered, math_store)
    rendered = enhance_html(rendered)
    return rendered, md.toc_tokens, bool(math_store)


def strip_tags(s: str) -> str:
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def flatten_toc(tokens: list, depth: int = 0) -> list[dict]:
    out = []
    for t in tokens:
        out.append({"id": t["id"], "name": strip_tags(t["name"]).rstrip("#").strip(), "level": t["level"]})
        out += flatten_toc(t.get("children", []), depth + 1)
    return out


# ── Models ────────────────────────────────────────────────────────────────

@dataclass
class Post:
    slug: str
    title: str
    date: dt.date
    category: str
    description: str
    html: str
    text: str
    toc: list
    has_math: bool
    legacy_urls: list = field(default_factory=list)
    updated: dt.date | None = None

    @property
    def url(self) -> str:
        return f"/writing/{self.slug}/"

    @property
    def minutes(self) -> int:
        return max(1, math.ceil(len(self.text.split()) / WORDS_PER_MINUTE))


def load_posts(site: dict) -> list[Post]:
    cats = {c["slug"] for c in site["writing_categories"]}
    posts = []
    for path in sorted((CONTENT / "posts").glob("*.md")):
        fm, body = read_front_matter(path)
        if fm.get("draft"):
            continue
        slug = fm.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
        if fm["category"] not in cats:
            raise SystemExit(f"{path.name}: unknown category {fm['category']!r}")
        rendered, toc, has_math = render_markdown(body)
        date = fm["date"] if isinstance(fm["date"], dt.date) else dt.date.fromisoformat(str(fm["date"]))
        posts.append(Post(
            slug=slug, title=fm["title"], date=date, category=fm["category"],
            description=fm.get("description", ""), html=rendered, text=strip_tags(rendered),
            toc=flatten_toc(toc), has_math=has_math, legacy_urls=fm.get("legacy_urls", []),
            updated=fm.get("updated"),
        ))
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts


def load_projects(site: dict) -> list[dict]:
    projects = site["projects"]
    for p in projects:
        p.setdefault("license", "")
        p["url"] = f"/projects/{p['slug']}/" if p.get("detail") else (p.get("repo") or p.get("demo") or "")
        p["placeholder"] = not p.get("summary")
        if p.get("detail"):
            fm, body = read_front_matter(CONTENT / "projects" / f"{p['slug']}.md")
            p.update({k: v for k, v in fm.items() if k not in p or not p[k]})
            p["body"], _, _ = render_markdown(body)
    return projects



# ── Project art (original, generative; not screenshots) ──────────────────

def project_art(motif: str, fit: str = "slice") -> str:
    W, H = 600, 400
    parts: list[str] = []
    if motif == "curve":
        # Forgetting curves reset by reviews at growing intervals (spaced repetition).
        x, y0, base = 40.0, 115.0, 330.0
        for k, span in enumerate([60, 90, 135, 200]):
            tau = 40 * (1.7 ** k)
            pts = []
            for i in range(41):
                dx = span * i / 40
                y = y0 + (base - y0) * (1 - math.exp(-dx / tau)) * 0.85
                pts.append(f"{x + dx:.1f},{y:.1f}")
            parts.append(f'<polyline class="art-ink" fill="none" stroke-width="3" stroke-linecap="round" points="{" ".join(pts)}"/>')
            end_y = float(pts[-1].split(",")[1])
            x += span
            parts.append(f'<line class="art-soft" x1="{x:.1f}" y1="{end_y:.1f}" x2="{x:.1f}" y2="{y0}" stroke-width="1.5" stroke-dasharray="4 5"/>')
            parts.append(f'<circle class="art-fill" cx="{x:.1f}" cy="{y0}" r="5"/>')
    elif motif == "ledger":
        for i in range(9):
            y = 60 + i * 32
            parts.append(f'<line class="art-soft" x1="60" y1="{y}" x2="{W - 60}" y2="{y}" stroke-width="1"/>')
        heights = [70, 110, 90, 150, 130, 190, 170, 230]
        for i, h in enumerate(heights):
            bx = 90 + i * 56
            parts.append(f'<rect class="art-fill" x="{bx}" y="{316 - h}" width="26" height="{h}" rx="4" opacity="{0.35 + 0.08 * i:.2f}"/>')
        pts = " ".join(f"{103 + i * 56},{316 - h - 18}" for i, h in enumerate(heights))
        parts.append(f'<polyline class="art-ink" fill="none" stroke-width="2.5" stroke-linejoin="round" points="{pts}"/>')
    elif motif == "track":
        def rail(off: float) -> str:
            return f"M -20 {300 + off} C 180 {300 + off}, 260 {120 + off}, 420 {120 + off} S 640 {60 + off}, 640 {60 + off}"
        for i in range(26):
            tt = i / 25
            # sleepers along an approximate centre line
            cx = -20 + 660 * tt
            cy = 300 - 180 * (3 * tt * tt - 2 * tt ** 3) - 40 * max(0, tt - 0.65)
            parts.append(f'<line class="art-soft" x1="{cx:.1f}" y1="{cy - 22:.1f}" x2="{cx:.1f}" y2="{cy + 22:.1f}" stroke-width="5" stroke-linecap="round"/>')
        parts.append(f'<path class="art-ink" d="{rail(-14)}" fill="none" stroke-width="3"/>')
        parts.append(f'<path class="art-ink" d="{rail(14)}" fill="none" stroke-width="3"/>')
        for cx, cy in [(110, 300), (330, 150), (520, 96)]:
            parts.append(f'<circle class="art-fill" cx="{cx}" cy="{cy - 46}" r="6"/>')
    else:  # grid
        for i in range(10):
            for j in range(7):
                parts.append(f'<circle class="art-fill" cx="{75 + i * 50}" cy="{55 + j * 50}" r="2.5" opacity=".45"/>')
        path = [(125, 105), (225, 105), (225, 205), (375, 205), (375, 305), (475, 305)]
        parts.append('<polyline class="art-ink" fill="none" stroke-width="3" stroke-linejoin="round" points="' +
                     " ".join(f"{a},{b}" for a, b in path) + '"/>')
        for a, b in path[::2]:
            parts.append(f'<circle class="art-fill" cx="{a}" cy="{b}" r="7"/>')
    return (f'<svg viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid {fit}" aria-hidden="true" focusable="false">'
            + "".join(parts) + "</svg>")

# ── Build ─────────────────────────────────────────────────────────────────

class Builder:
    def __init__(self) -> None:
        self.site = yaml.safe_load((CONTENT / "site.yml").read_text(encoding="utf-8"))
        self.site["build_year"] = dt.date.today().year
        self.cat_names = {c["slug"]: c["name"] for c in self.site["writing_categories"]}
        self.posts = load_posts(self.site)
        self.projects = load_projects(self.site)
        self.pages: list[tuple[str, dt.date | None]] = []
        self.pending: list[tuple[Path, str]] = []
        self.env = Environment(loader=FileSystemLoader(TEMPLATES),
                               autoescape=select_autoescape(["html", "xml"]),
                               trim_blocks=True, lstrip_blocks=True)
        self.env.filters["date_long"] = lambda d: f"{d:%B} {d.day}, {d.year}"
        self.env.filters["date_short"] = lambda d: f"{d:%b} {d.day}, {d.year}"
        self.env.filters["absurl"] = lambda u: self.site["url"] + u if u.startswith("/") else u
        self.env.filters["is_external"] = lambda u: bool(re.match(r"https?://", u or ""))
        self.env.globals.update(site=self.site, cat_names=self.cat_names, project_art=project_art,
                                css_version=self.asset_version("css/main.css"),
                                js_version=self.asset_version("js/main.js"))

    def asset_version(self, rel: str) -> str:
        import hashlib
        return hashlib.sha1((STATIC / rel).read_bytes()).hexdigest()[:8]

    def write(self, route: str, content: str, lastmod: dt.date | None = None, sitemap: bool = True) -> None:
        path = OUT / route.lstrip("/")
        if route.endswith("/"):
            path = path / "index.html"
        self.pending.append((path, content))
        if sitemap:
            self.pages.append((route, lastmod))

    MATH_RE = re.compile(r'<(span|div) class="math-(inline|display)">\\[(\[](.*?)\\[)\]]</\1>', re.S)

    def flush(self) -> None:
        """Render all math in one KaTeX call, then write every page."""
        jobs: list[dict] = []
        for _, content in self.pending:
            for m in self.MATH_RE.finditer(content):
                jobs.append({"tex": html.unescape(m.group(3)), "display": m.group(2) == "display"})
        rendered: list[str] = []
        if jobs:
            proc = subprocess.run(["node", str(ROOT / "scripts" / "render_math.js")], input=json.dumps(jobs),
                                  capture_output=True, text=True, check=True)
            if proc.stderr:
                print(proc.stderr, file=sys.stderr)
            rendered = json.loads(proc.stdout)
        it = iter(rendered)
        for path, content in self.pending:
            content = self.MATH_RE.sub(lambda m: f'<{m.group(1)} class="math-{m.group(2)}">{next(it)}</{m.group(1)}>', content)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        print(f"Rendered {len(jobs)} equations with KaTeX")

    def render(self, template: str, route: str, **ctx) -> None:
        ctx.setdefault("canonical", route)
        ctx.setdefault("nav", route.strip("/").split("/")[0] or "home")
        self.write(route, self.env.get_template(template).render(route=route, **ctx),
                   ctx.pop("lastmod", None), ctx.pop("sitemap", True))

    def run(self) -> None:
        if OUT.exists():
            shutil.rmtree(OUT)
        shutil.copytree(STATIC, OUT)
        (OUT / ".nojekyll").write_text("")

        featured = [p for p in self.projects if p.get("featured")]
        latest = self.posts[0].date if self.posts else None

        self.render("home.html", "/", featured=featured, recent=self.posts[:3], lastmod=latest,
                    title=None, description=self.site["description"])
        self.render("about.html", "/about/", title="About",
                    description="Background, education and interests of Mehedi Ackerman: physics undergraduate at GSTU, cyber security analyst and software developer.")
        sec_posts = [p for p in self.posts if p.category == "cybersecurity"]
        self.render("security.html", "/security/", title="Cybersecurity", posts=sec_posts,
                    description="Cybersecurity interests, certifications and security engineering in practice.")
        self.render("projects.html", "/projects/", title="Projects", projects=self.projects,
                    description="Software projects: Android apps, browser extensions and scientific computing tools.")
        detail = [p for p in self.projects if p.get("detail")]
        for i, p in enumerate(detail):
            self.render("project.html", p["url"], title=p["name"], project=p,
                        next_project=detail[(i + 1) % len(detail)], description=p["summary"], nav="projects")
        phys_posts = [p for p in self.posts if p.category in ("physics", "notes")]
        self.render("physics.html", "/physics/", title="Physics", posts=phys_posts, has_math=True,
                    description="Physics at GSTU: academic and research interests, problem solutions and notes.")
        cats_used = [c for c in self.site["writing_categories"] if any(p.category == c["slug"] for p in self.posts)]
        self.render("writing.html", "/writing/", title="Writing", posts=self.posts, categories=cats_used,
                    lastmod=latest, description="Essays, notes and problem solutions on physics, software and security.")
        for i, post in enumerate(self.posts):
            related = [p for p in self.posts if p is not post and p.category == post.category][:2]
            related += [p for p in self.posts if p is not post and p not in related][: 2 - len(related)]
            self.render("post.html", post.url, title=post.title, post=post, related=related,
                        newer=self.posts[i - 1] if i > 0 else None,
                        older=self.posts[i + 1] if i + 1 < len(self.posts) else None,
                        has_math=post.has_math, description=post.description,
                        lastmod=post.updated or post.date, og_type="article", nav="writing")
        self.render("contact.html", "/contact/", title="Contact",
                    description="How to reach Mehedi Ackerman: email, GitHub and LinkedIn.")
        self.render("404.html", "/404.html", title="Page not found", sitemap=False, noindex=True,
                    canonical="/404.html", description="This page does not exist.")

        self.redirects()
        self.flush()
        self.feeds()
        self.write_highlight_css()
        print(f"Built {len(self.pages)} pages, {len(self.posts)} posts → {OUT.relative_to(ROOT)}/")

    # Old Jekyll URLs keep working.
    def redirects(self) -> None:
        tpl = self.env.get_template("redirect.html")
        legacy = {"/cs/": "/writing/?category=software", "/thoughts/": "/writing/?category=reflections"}
        for post in self.posts:
            for u in post.legacy_urls:
                legacy[u] = post.url
        for old, new in legacy.items():
            self.write(old, tpl.render(target=new), sitemap=False)

    def feeds(self) -> None:
        url = self.site["url"]
        items = "".join(
            f"<item><title>{xml_escape(p.title)}</title><link>{url}{p.url}</link>"
            f"<guid isPermaLink=\"true\">{url}{p.url}</guid>"
            f"<pubDate>{dt.datetime.combine(p.date, dt.time(9)).strftime('%a, %d %b %Y %H:%M:%S +0600')}</pubDate>"
            f"<category>{xml_escape(self.cat_names[p.category])}</category>"
            f"<description>{xml_escape(p.description)}</description></item>"
            for p in self.posts)
        rss = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
               f"<title>{xml_escape(self.site['title'])} — Writing</title><link>{url}/writing/</link>"
               f"<description>{xml_escape(self.site['description'])}</description><language>en</language>"
               f'<atom:link href="{url}/feed.xml" rel="self" type="application/rss+xml"/>{items}</channel></rss>\n')
        (OUT / "feed.xml").write_text(rss, encoding="utf-8")

        urls = "".join(
            f"<url><loc>{url}{r}</loc>{f'<lastmod>{d.isoformat()}</lastmod>' if d else ''}</url>"
            for r, d in self.pages)
        (OUT / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {url}/sitemap.xml\n", encoding="utf-8")

        index = [{"t": p.title, "u": p.url, "c": p.category, "d": p.description,
                  "x": p.text[:6000]} for p in self.posts]
        (OUT / "search.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    def write_highlight_css(self) -> None:
        light = HtmlFormatter(style="friendly").get_style_defs(".highlight")
        dark = HtmlFormatter(style="github-dark").get_style_defs('[data-theme="dark"] .highlight')
        dark_sys = HtmlFormatter(style="github-dark").get_style_defs(':root:not([data-theme]) .highlight')
        css = (f"/* generated by build.py — Pygments */\n{light}\n{dark}\n"
               f"@media (prefers-color-scheme: dark) {{\n{dark_sys}\n}}\n")
        # Backgrounds are set by main.css so code blocks match the theme surfaces.
        css = re.sub(r"\.highlight \{ background: [^;]+; \}", "", css)
        css = re.sub(r"(\.highlight|\[data-theme=\"dark\"\] \.highlight|:root:not\(\[data-theme\]\) \.highlight) \{ background: [^}]*\}", "", css)
        (OUT / "css" / "highlight.css").write_text(css, encoding="utf-8")


def serve() -> None:
    import functools
    import http.server
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
    print("Serving on http://localhost:8000 (Ctrl+C to stop)")
    http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()


if __name__ == "__main__":
    Builder().run()
    if "--serve" in sys.argv:
        serve()
