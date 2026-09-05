# Lagrangian

Source for [euler16.github.io](https://euler16.github.io), a personal blog built with [Jekyll](https://jekyllrb.com/) and deployed with GitHub Pages.

## Prerequisites

Install Ruby 2.6 or newer and Bundler. On macOS, a version manager such as `rbenv` is recommended so that the system Ruby is left untouched.

```sh
gem install --user-install bundler -v "~> 2.4.0"
export PATH="$(ruby -r rubygems -e 'puts Gem.user_dir')/bin:$PATH"
bundle config set --local path vendor/bundle
bundle install
```

The user-local install and `vendor/bundle` directory avoid modifying macOS's protected system Ruby. Add the `export PATH=...` line to your shell profile if you use this setup regularly. `bundle install` downloads the Jekyll and plugin versions declared in `Gemfile`. Run it again after pulling changes to that file.

## Edit the site

The main authoring locations are:

- `_posts/` — blog posts.
- `about.md`, `cs.md`, `mathematics.md`, and `thoughts.md` — standalone pages and post-category archives.
- `_layouts/` and `_includes/` — shared HTML templates, navigation, footer, metadata, and analytics includes.
- `_sass/` and `css/style.scss` — site styles.
- `assets/` — images, PDFs, and other static files.
- `assets/vendor/mathjax/` — the local MathJax 3 library used for equations.
- `_config.yml` — site-wide details such as title, social accounts, URL, pagination, and plugins.

Changes to `_config.yml` require restarting the local server. Keep asset paths relative to the site root, for example `{{ site.baseurl }}/assets/example.png`, so that they also work if a `baseurl` is configured later.

## Add a blog post

1. Create `_posts/YYYY-MM-DD-a-short-slug.markdown`. The date in the filename determines the post URL and publication date.
2. Start it with YAML front matter. Use an existing category (`cs`, `mathematics`, or `thoughts`) if the post should appear on that archive page.
3. Write the body in Markdown. Place accompanying images in a descriptive subdirectory under `assets/` and reference them using `{{ site.baseurl }}`.

```markdown
---
layout: post
title: "My post title"
date: 2026-09-05 10:00:00 +0100
categories: thoughts
author: "Nilay Shrivastava"
comments: true
---

Your post starts here.

![Helpful alt text]({{ site.baseurl }}/assets/my-post/example.png)
```

Use a publication date that is not in the future. To preview a deliberately future-dated post, add `--future` to the serve command below.

## Preview locally

Run the development server from the repository root:

```sh
bundle exec jekyll serve --livereload
```

Open <http://127.0.0.1:4000>. Jekyll regenerates the site after most content, layout, and style changes; restart it after configuration changes. Stop the server with `Ctrl-C`.

## Build and test locally

This repository does not currently contain an automated test suite. A strict Jekyll build is the baseline check before publishing:

```sh
bundle exec jekyll build --strict_front_matter
```

The generated site is written to `_site/` (which is intentionally ignored by Git). Before pushing, also open the home page, the new post, and its category archive in the local preview to check links, images, math, and pagination.

## Publishing and the deployment branch

GitHub Pages publishes this user site from the branch configured in the repository's **Settings → Pages**. This repository currently has `master` as its GitHub default branch and no GitHub Actions deployment workflow, so pushes to the branch selected there are the relevant deployment trigger.

Renaming `master` to `main` is optional: it does not improve the site or GitHub Pages deployment by itself. `main` is the modern GitHub convention, so rename it if consistency with newer repositories is valuable, but first change the default branch in GitHub and then verify **Settings → Pages** points to `main` and the repository root. Update local clones afterwards with:

```sh
git fetch origin
git branch -m master main
git branch -u origin/main main
```

If the existing `master` setup is deploying reliably, leaving it unchanged is the lowest-risk choice.

## License

See [LICENSE.txt](LICENSE.txt).
