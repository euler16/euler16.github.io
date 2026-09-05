# MathJax 3.2.2

This directory vendors the `es5/tex-mml-svg.js` combined component from the
[`mathjax` 3.2.2 npm package](https://www.npmjs.com/package/mathjax/v/3.2.2).
It supports TeX (including AMS extensions) and MathML input, and renders SVG
output without fetching web fonts or other MathJax assets at runtime. The
MathJax contextual menu is disabled so that its optional accessibility
extensions cannot be downloaded dynamically.

The site loads it through `js/mathjax-config.js`. The configuration preserves
the blog's `\\(...\\)`, `$...$`, `\\[...\\]`, and `$$...$$` delimiters.

The bundled file's SHA-256 is:

```
1f17a7ed95ff4a4b27d16bf0fb5f80b915686ee8673e82983a2876ecf8cb9fae
```

MathJax is licensed under Apache-2.0; the upstream license is included as
`LICENSE.txt`.
