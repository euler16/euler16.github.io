// Pre-renders TeX to HTML with KaTeX at build time (no math JS ships to readers).
// stdin: JSON [{tex, display}]  →  stdout: JSON [html]
const katex = require("./vendor/katex.min.js");
let input = "";
process.stdin.on("data", (d) => (input += d));
process.stdin.on("end", () => {
  const items = JSON.parse(input);
  const macros = { "\\bold": "\\mathbf{#1}" };
  const out = items.map(({ tex, display }) => {
    try {
      return katex.renderToString(tex, { displayMode: display, throwOnError: true, macros, strict: "ignore", output: "htmlAndMathml" });
    } catch (e) {
      process.stderr.write(`KaTeX error: ${e.message}\n  in: ${tex}\n`);
      return katex.renderToString(tex, { displayMode: display, throwOnError: false, macros, strict: "ignore" });
    }
  });
  process.stdout.write(JSON.stringify(out));
});
