# mehedieh.github.io

Personal site of Mehedi Ackerman: cybersecurity, software development and physics.
Live at **https://mehedieh.github.io**.

The site is plain static HTML built by a small Python script (`build.py`). There's no
front-end framework, no web fonts and no trackers. Math is rendered to HTML at build
time with KaTeX, so readers don't download a math library.

## Structure

```text
content/
  site.yml            ← name, links, skills, certifications, projects, physics interests
  posts/*.md          ← articles (front matter + Markdown, $…$ and $$…$$ for math)
  projects/*.md       ← case-study pages for projects with `detail: true` in site.yml
templates/            ← Jinja2 layouts (base, home, about, security, projects, post, …)
static/
  css/main.css        ← design tokens (light + dark), layout and components
  js/main.js          ← theme toggle, menu, filters, search, pendulum, reading progress
  img/                ← portrait, post figures, brand assets
  katex/              ← KaTeX stylesheet and fonts (self-hosted)
scripts/
  render_math.js      ← build-time KaTeX renderer (uses scripts/vendor/katex.min.js)
  make_brand.py       ← regenerates favicon, touch icon and social card
build.py              ← builds everything into _site/
.github/workflows/pages.yml  ← builds and deploys to GitHub Pages on every push
```

## Build locally

You need Python 3.10 or newer and Node.js 18 or newer (Node is only used to run KaTeX).

```bash
pip install -r requirements.txt
python build.py            # → _site/
python build.py --serve    # build, then preview at http://localhost:8000
```

## Deploy (one-time setup)

1. Push this repository to `mehedieh/mehedieh.github.io` on the `master` (or `main`) branch.
2. On GitHub, open **Settings → Pages → Build and deployment** and set **Source** to **GitHub Actions**.
   *(The old site used "Deploy from a branch" with Jekyll. That setting must be changed,
   or GitHub will try to run Jekyll on this repository and the site will not build.)*
3. Every push now runs `.github/workflows/pages.yml`, which builds `_site/` and publishes it.
   Progress is shown under the **Actions** tab.

Every page is generated as `folder/index.html`, so refreshing a nested URL
(`/writing/morin-mechanics-2-1/`) works on GitHub Pages. Old Jekyll URLs
(`/physics/2022/08/03/kirchhoffs-law.html`, `/cs/`, `/thoughts/`, …) redirect to their new pages.

## Writing a new post

Create `content/posts/YYYY-MM-DD-short-slug.md`:

```markdown
---
title: "Your title"
date: 2026-12-01
category: cybersecurity      # cybersecurity | software | physics | notes | technology | reflections
description: "One or two sentences shown in lists, search results and link previews."
---

Body in Markdown. Use ## for sections. Inline math: $E = mc^2$. Display math:

$$
\oint \mathbf{E}\cdot d\mathbf{l} = -\frac{d\Phi_B}{dt}
$$
```

Put images in `static/img/posts/` and reference them as `/img/posts/name.png`.
Add `draft: true` to keep a post out of the build. The URL becomes `/writing/short-slug/`.
Reading time, table of contents (3+ headings), syntax highlighting, RSS, sitemap and search
index are all generated automatically.

## Editing your details

Almost everything personal lives in `content/site.yml`. Empty values are simply not rendered,
so nothing fake ever appears. In particular:

- `certifications` — add the CCEP issuer, date, credential ID and verification URL.
- `links.cv` — drop a PDF into `static/files/` and set e.g. `/files/cv.pdf` to show a download button.
- `education` — confirm the degree wording and add years.
- `projects` — GSTU Physics Smart Campus needs a summary, stack and repository link.

If you change the name or tagline, run `python scripts/make_brand.py` to regenerate the social card.
