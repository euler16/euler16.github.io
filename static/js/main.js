/* mehedieh.github.io — progressive enhancement only; every page works without JS. */
(() => {
  "use strict";
  const doc = document.documentElement;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));

  /* ---------------- Theme ---------------- */
  const themeMedia = window.matchMedia("(prefers-color-scheme: dark)");
  const stored = () => { try { return localStorage.getItem("theme"); } catch { return null; } };
  const applyTheme = (t) => {
    doc.setAttribute("data-theme", t);
    const meta = $('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", t === "dark" ? "#0c0d10" : "#fbfbf9");
    $$(".theme-toggle").forEach((b) => {
      b.setAttribute("aria-label", t === "dark" ? "Switch to light theme" : "Switch to dark theme");
      b.setAttribute("aria-pressed", String(t === "dark"));
    });
    document.dispatchEvent(new CustomEvent("themechange"));
  };
  applyTheme(doc.getAttribute("data-theme") || (themeMedia.matches ? "dark" : "light"));
  $$(".theme-toggle").forEach((btn) => btn.addEventListener("click", () => {
    const next = doc.getAttribute("data-theme") === "dark" ? "light" : "dark";
    try { localStorage.setItem("theme", next); } catch {}
    applyTheme(next);
  }));
  themeMedia.addEventListener?.("change", (e) => { if (!stored()) applyTheme(e.matches ? "dark" : "light"); });

  /* ---------------- Header + mobile nav ---------------- */
  const header = $(".site-header");
  const onScroll = () => header && header.classList.toggle("is-scrolled", window.scrollY > 4);
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  const menuBtn = $(".menu-toggle");
  const menu = $("#mobile-nav");
  if (menuBtn && menu) {
    const setOpen = (open) => {
      menuBtn.setAttribute("aria-expanded", String(open));
      menuBtn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      menu.classList.toggle("is-open", open);
      menu.inert = !open;
      document.body.classList.toggle("menu-open", open);
      if (open) $("a", menu)?.focus();
    };
    menu.inert = true;
    menuBtn.addEventListener("click", () => setOpen(menuBtn.getAttribute("aria-expanded") !== "true"));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && menu.classList.contains("is-open")) { setOpen(false); menuBtn.focus(); }
    });
    window.matchMedia("(min-width: 880px)").addEventListener?.("change", (e) => e.matches && setOpen(false));
  }

  /* ---------------- Reveal ---------------- */
  const hero = $(".hero");
  if (hero) requestAnimationFrame(() => requestAnimationFrame(() => hero.classList.add("is-ready")));
  const observed = $$("[data-observe]");
  if (observed.length && "IntersectionObserver" in window && !reduceMotion.matches) {
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (en.isIntersecting) { en.target.classList.add("is-visible"); io.unobserve(en.target); }
    }), { rootMargin: "0px 0px -8% 0px" });
    observed.forEach((el) => io.observe(el));
  } else observed.forEach((el) => el.classList.add("is-visible"));

  /* ---------------- Double pendulum ----------------
     Equal masses and lengths; equations of motion from the Lagrangian,
     integrated with fourth-order Runge–Kutta. Drag either bob to set it. */
  function Pendulum(canvas) {
    const ctx = canvas.getContext("2d");
    const G = 9.81, L = 1, M = 1;
    let s = [Math.PI * 0.62, Math.PI * 0.98, 0, 0]; // θ1, θ2, ω1, ω2
    const initial = s.slice();
    const trail = [];
    const TRAIL = 1100;
    let running = !reduceMotion.matches, visible = true, drag = 0, raf = 0, last = 0;
    let W = 0, H = 0, dpr = 1, scale = 1, ox = 0, oy = 0;
    let ink = "28,28,30", accent = "10,95,209";

    const readColors = () => {
      const cs = getComputedStyle(doc);
      ink = cs.getPropertyValue("--pendulum-ink").trim() || ink;
      accent = cs.getPropertyValue("--pendulum-accent").trim() || accent;
    };
    const deriv = ([t1, t2, w1, w2]) => {
      const d = t1 - t2, den = 2 * M + M - M * Math.cos(2 * t1 - 2 * t2);
      const a1 = (-G * (2 * M + M) * Math.sin(t1) - M * G * Math.sin(t1 - 2 * t2)
        - 2 * Math.sin(d) * M * (w2 * w2 * L + w1 * w1 * L * Math.cos(d))) / (L * den);
      const a2 = (2 * Math.sin(d) * (w1 * w1 * L * (M + M) + G * (M + M) * Math.cos(t1)
        + w2 * w2 * L * M * Math.cos(d))) / (L * den);
      return [w1, w2, a1, a2];
    };
    const rk4 = (h) => {
      const add = (a, b, k) => a.map((v, i) => v + b[i] * k);
      const k1 = deriv(s), k2 = deriv(add(s, k1, h / 2)), k3 = deriv(add(s, k2, h / 2)), k4 = deriv(add(s, k3, h));
      s = s.map((v, i) => v + (h / 6) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]));
    };
    const points = () => {
      const x1 = ox + scale * Math.sin(s[0]), y1 = oy + scale * Math.cos(s[0]);
      return [x1, y1, x1 + scale * Math.sin(s[1]), y1 + scale * Math.cos(s[1])];
    };
    const resize = () => {
      const r = canvas.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = r.width; H = r.height;
      canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      scale = Math.min(W, H) * 0.235; ox = W / 2; oy = H / 2;
      trail.length = 0;
      draw();
    };
    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      // Faint reach circle: the configuration space boundary of the outer bob.
      ctx.strokeStyle = `rgba(${ink},0.07)`; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(ox, oy, scale * 2, 0, Math.PI * 2); ctx.stroke();
      ctx.setLineDash([2, 5]);
      ctx.beginPath(); ctx.arc(ox, oy, scale, 0, Math.PI * 2); ctx.stroke();
      ctx.setLineDash([]);
      // Trail, drawn in alpha bands so a long history stays cheap.
      ctx.lineCap = "round"; ctx.lineJoin = "round";
      const n = trail.length, bands = 36;
      for (let b = 0; b < bands; b++) {
        const i0 = Math.floor((b * n) / bands), i1 = Math.min(n - 1, Math.floor(((b + 1) * n) / bands));
        if (i1 <= i0) continue;
        const a = (b + 1) / bands;
        ctx.strokeStyle = `rgba(${accent},${(0.06 + a * a * 0.85).toFixed(3)})`;
        ctx.lineWidth = 0.7 + a * 1.3;
        ctx.beginPath(); ctx.moveTo(trail[i0][0], trail[i0][1]);
        for (let i = i0 + 1; i <= i1; i++) ctx.lineTo(trail[i][0], trail[i][1]);
        ctx.stroke();
      }
      const [x1, y1, x2, y2] = points();
      ctx.strokeStyle = `rgba(${ink},0.9)`; ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.moveTo(ox, oy); ctx.lineTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
      ctx.fillStyle = `rgba(${ink},1)`;
      ctx.beginPath(); ctx.arc(ox, oy, 2.5, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.arc(x1, y1, 5.5, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = `rgba(${accent},1)`;
      ctx.beginPath(); ctx.arc(x2, y2, 6.5, 0, Math.PI * 2); ctx.fill();
    };
    const step = (dt) => {
      const sub = 8, h = Math.min(dt, 1 / 30) * 1.15 / sub;
      for (let i = 0; i < sub; i++) rk4(h);
      const p = points(); trail.push([p[2], p[3]]);
      if (trail.length > TRAIL) trail.shift();
    };
    const loop = (t) => {
      raf = 0;
      if (!running || !visible || document.hidden) { last = 0; return; }
      const dt = last ? (t - last) / 1000 : 1 / 60; last = t;
      if (!drag) step(dt);
      draw();
      raf = requestAnimationFrame(loop);
    };
    const kick = () => { if (!raf && running && visible) raf = requestAnimationFrame(loop); };

    // Pointer interaction
    const local = (e) => { const r = canvas.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
    canvas.addEventListener("pointerdown", (e) => {
      const [px, py] = local(e), [x1, y1, x2, y2] = points();
      const d2 = Math.hypot(px - x2, py - y2), d1 = Math.hypot(px - x1, py - y1);
      drag = d2 < 28 ? 2 : d1 < 28 ? 1 : 0;
      if (drag) { canvas.setPointerCapture(e.pointerId); trail.length = 0; e.preventDefault(); }
    });
    canvas.addEventListener("pointermove", (e) => {
      if (!drag) return;
      const [px, py] = local(e);
      if (drag === 1) s[0] = Math.atan2(px - ox, py - oy);
      else { const x1 = ox + scale * Math.sin(s[0]), y1 = oy + scale * Math.cos(s[0]); s[1] = Math.atan2(px - x1, py - y1); }
      s[2] = s[3] = 0; draw();
    });
    const release = () => { if (drag) { drag = 0; running = true; kick(); } };
    canvas.addEventListener("pointerup", release);
    canvas.addEventListener("pointercancel", release);

    if ("IntersectionObserver" in window) {
      new IntersectionObserver(([en]) => { visible = en.isIntersecting; kick(); }).observe(canvas);
    }
    document.addEventListener("visibilitychange", kick);
    document.addEventListener("themechange", () => { readColors(); draw(); });
    window.addEventListener("resize", () => { resize(); });

    readColors(); resize();
    if (!running) { for (let i = 0; i < 240; i++) step(1 / 60); draw(); } // reduced motion: a still frame with history
    kick();

    return {
      reset() { s = initial.slice(); trail.length = 0; draw(); kick(); },
      toggle() { running = !running; kick(); return running; },
      get running() { return running; },
    };
  }

  $$("canvas[data-pendulum]").forEach((c) => {
    const p = Pendulum(c);
    const scope = c.closest("[data-pendulum-scope]") || document;
    $$("[data-pendulum-reset]", scope).forEach((b) => b.addEventListener("click", () => p.reset()));
    $$("[data-pendulum-toggle]", scope).forEach((b) => {
      const label = () => { b.textContent = p.running ? "Pause" : "Play"; b.setAttribute("aria-pressed", String(!p.running)); };
      label();
      b.addEventListener("click", () => { p.toggle(); label(); });
    });
  });

  /* ---------------- Project filters ---------------- */
  const projFilters = $("[data-project-filters]");
  if (projFilters) {
    const cards = $$(".project-grid [data-project-category]");
    const status = $("#project-filter-status");
    projFilters.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-filter]");
      if (!btn) return;
      const f = btn.dataset.filter;
      $$("button[data-filter]", projFilters).forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
      let n = 0;
      cards.forEach((c) => { const show = f === "all" || c.dataset.projectCategory === f; c.hidden = !show; if (show) n++; });
      if (status) status.textContent = `${n} project${n === 1 ? "" : "s"} shown`;
    });
  }

  /* ---------------- Writing search + category filter ---------------- */
  const writing = $("[data-writing]");
  if (writing) {
    const input = $("#post-search", writing);
    const rows = $$(".post-row", writing);
    const chips = $$("button[data-category]", writing);
    const empty = $("[data-empty]", writing);
    const status = $("#post-filter-status");
    let index = null, cat = "all";
    const params = new URLSearchParams(location.search);
    if (params.get("category") && chips.some((c) => c.dataset.category === params.get("category"))) cat = params.get("category");
    if (params.get("q")) input.value = params.get("q");

    const loadIndex = () => index ? Promise.resolve(index) :
      fetch("/search.json").then((r) => r.json()).then((d) => (index = new Map(d.map((p) => [p.u, (p.t + " " + p.d + " " + p.x).toLowerCase()]))))
        .catch(() => (index = new Map()));
    const apply = () => {
      const terms = input.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
      let n = 0;
      rows.forEach((r) => {
        const hay = (index && index.get(r.dataset.url)) || r.textContent.toLowerCase();
        const show = (cat === "all" || r.dataset.category === cat) && terms.every((t) => hay.includes(t));
        r.hidden = !show; if (show) n++;
      });
      chips.forEach((c) => c.setAttribute("aria-pressed", String(c.dataset.category === cat)));
      empty.hidden = n !== 0;
      if (status) status.textContent = `${n} article${n === 1 ? "" : "s"} shown`;
      const q = new URLSearchParams();
      if (cat !== "all") q.set("category", cat);
      if (input.value.trim()) q.set("q", input.value.trim());
      history.replaceState(null, "", location.pathname + (q.toString() ? "?" + q : ""));
    };
    chips.forEach((c) => c.addEventListener("click", () => { cat = c.dataset.category; apply(); }));
    input.addEventListener("focus", () => loadIndex().then(apply), { once: true });
    input.addEventListener("input", () => loadIndex().then(apply));
    $("[data-clear]", writing)?.addEventListener("click", () => { input.value = ""; cat = "all"; apply(); input.focus(); });
    if (params.get("q")) loadIndex().then(apply); else apply();
  }

  /* ---------------- Article: progress, TOC, share, copy ---------------- */
  const article = $("[data-article]");
  if (article) {
    const bar = $(".progress span");
    const update = () => {
      const r = article.getBoundingClientRect();
      const total = r.height - window.innerHeight;
      const p = total > 0 ? Math.min(1, Math.max(0, -r.top / total)) : 1;
      if (bar) bar.style.transform = `scaleX(${p})`;
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);

    const links = $$(".toc a");
    if (links.length && "IntersectionObserver" in window) {
      const map = new Map(links.map((a) => [decodeURIComponent(a.hash.slice(1)), a]));
      const heads = $$("h2[id], h3[id]", article).filter((h) => map.has(h.id));
      const io = new IntersectionObserver((entries) => {
        entries.forEach((en) => {
          if (en.isIntersecting) { links.forEach((l) => l.classList.remove("is-active")); map.get(en.target.id)?.classList.add("is-active"); }
        });
      }, { rootMargin: "-15% 0px -70% 0px" });
      heads.forEach((h) => io.observe(h));
    }

    $$(".highlight", article).forEach((block) => {
      const btn = document.createElement("button");
      btn.type = "button"; btn.className = "copy-btn"; btn.textContent = "Copy";
      btn.addEventListener("click", async () => {
        try { await navigator.clipboard.writeText($("pre", block).innerText); btn.textContent = "Copied"; }
        catch { btn.textContent = "Press Ctrl+C"; }
        setTimeout(() => (btn.textContent = "Copy"), 1600);
      });
      block.appendChild(btn);
    });
  }

  $$("[data-share]").forEach((btn) => {
    const label = btn.querySelector("span") || btn;
    const original = label.textContent;
    btn.addEventListener("click", async () => {
      const data = { title: btn.dataset.title || document.title, url: btn.dataset.url || location.href };
      if (navigator.share) { try { await navigator.share(data); } catch {} return; }
      try { await navigator.clipboard.writeText(data.url); label.textContent = "Link copied"; }
      catch { label.textContent = "Copy the address bar link"; }
      setTimeout(() => (label.textContent = original), 1800);
    });
  });

})();
