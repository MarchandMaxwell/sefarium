/* Sefarium reader for the Greek-only Plato pages.
   Two views, as on Sefaria: the contents page (title, Start Reading, Stephanus
   pages, About This Text) and the reader (one column of speeches with the
   Stephanus numbers in the margin, a display menu, and a Resources panel).
   The text itself is plain HTML in the page; this script only arranges it. */
(function () {
  "use strict";
  var doc = document.documentElement;
  var body = document.body;
  var reading = document.querySelector(".reading");
  if (!reading) return;
  var title = body.getAttribute("data-title") || "";
  var urn = body.getAttribute("data-urn") || "";
  var $ = function (id) { return document.getElementById(id); };

  /* ---------- a viewer's own choices, kept in this browser only ---------- */
  var prefs = { scale: 1, accents: true };
  try { var saved = JSON.parse(localStorage.getItem("sefarium-greek") || "{}"); if (saved && typeof saved === "object") { if (typeof saved.scale === "number") prefs.scale = saved.scale; if (typeof saved.accents === "boolean") prefs.accents = saved.accents; } } catch (e) {}
  function savePrefs() { try { localStorage.setItem("sefarium-greek", JSON.stringify(prefs)); } catch (e) {} }

  /* ---------- the section in force at the start of each speech ---------- */
  var segs = Array.prototype.slice.call(reading.querySelectorAll("p"));
  var current = "";
  var startOf = new Map();
  var walker = document.createTreeWalker(reading, NodeFilter.SHOW_ELEMENT, null);
  var node, segIndex = 0;
  while ((node = walker.nextNode())) {
    if (node.tagName === "P") { startOf.set(node, current); }
    if (node.classList && node.classList.contains("steph")) {
      var p = node.closest("p");
      var n = (node.textContent || "").trim();
      // a number at the very start of a speech belongs to that speech
      if (p && startOf.get(p) !== undefined && !textBefore(p, node)) startOf.set(p, n);
      current = n;
    }
  }
  function textBefore(p, el) {
    var r = document.createRange(); r.setStart(p, 0); r.setEndBefore(el);
    var t = r.toString().replace(/\s+/g, " ").trim();
    var spk = p.querySelector(".spk");
    if (spk && t.indexOf((spk.textContent || "").trim()) === 0) t = t.slice((spk.textContent || "").trim().length).trim();
    return t.length > 0;
  }
  segs.forEach(function (p, i) { p.tabIndex = 0; p.setAttribute("data-i", i); if (!startOf.get(p)) startOf.set(p, firstSection()); });
  function firstSection() { var a = reading.querySelector(".steph"); return a ? a.textContent.trim() : ""; }
  // the number to show in the margin: the first section mark inside the speech
  segs.forEach(function (p) { var a = p.querySelector(".steph"); if (a && !textBefore(p, a)) p.classList.add("starts"); });

  /* ---------- views: contents or reader ---------- */
  function showReader(on) {
    body.classList.toggle("v-reader", on);
    body.classList.toggle("v-contents", !on);
    setBarHeights();
  }
  function route() {
    var h = decodeURIComponent(location.hash.slice(1));
    if (!h || h === "contents") { showReader(false); window.scrollTo(0, 0); return; }
    var el = $(h);
    if (el && reading.contains(el)) {
      showReader(true);
      requestAnimationFrame(function () { el.scrollIntoView({ block: "start" }); updateRef(); });
    } else if (el) {
      showReader(false); el.scrollIntoView({ block: "start" });
    }
  }
  window.addEventListener("hashchange", route);

  /* ---------- live citation in the reader bar ---------- */
  var refEl = $("rb-ref");
  function barBottom() { var rb = document.querySelector(".rbar"); return rb ? rb.getBoundingClientRect().bottom : 0; }
  function setBarHeights() {
    var sb = document.querySelector(".sitebar");
    doc.style.setProperty("--siteh", (sb ? sb.getBoundingClientRect().height : 0) + "px");
    var rb = document.querySelector(".rbar");
    doc.style.setProperty("--barh", ((sb ? sb.getBoundingClientRect().height : 0) + (rb && body.classList.contains("v-reader") ? rb.getBoundingClientRect().height : 0)) + "px");
  }
  function sectionAt(y) {
    var col = reading.getBoundingClientRect();
    var el = document.elementFromPoint(col.left + Math.min(col.width / 2, 200), y);
    var p = el && el.closest ? el.closest("p") : null;
    if (!p || !reading.contains(p)) return null;
    // the last section mark above the line
    var marks = p.querySelectorAll(".steph"), last = startOf.get(p);
    for (var i = 0; i < marks.length; i++) { if (marks[i].getBoundingClientRect().top <= y + 4) last = marks[i].textContent.trim(); }
    return last;
  }
  var selected = null;
  function updateRef() {
    if (!refEl || !body.classList.contains("v-reader")) return;
    var s = selected ? startOf.get(selected) : sectionAt(barBottom() + 30);
    if (s) refEl.textContent = s;
  }
  var ticking = false;
  window.addEventListener("scroll", function () { if (ticking) return; ticking = true; requestAnimationFrame(function () { ticking = false; updateRef(); }); }, { passive: true });
  window.addEventListener("resize", setBarHeights);

  /* ---------- display options ---------- */
  var menu = $("rmenu"), abtn = $("rb-a");
  function syncMenu() {
    doc.style.setProperty("--scale", prefs.scale);
    var sw = $("sw-acc"); if (sw) sw.setAttribute("aria-checked", String(prefs.accents));
  }
  if (abtn && menu) {
    abtn.addEventListener("click", function (e) { menu.hidden = !menu.hidden; abtn.setAttribute("aria-expanded", String(!menu.hidden)); e.stopPropagation(); });
    document.addEventListener("click", function (e) { if (!menu.hidden && !menu.contains(e.target)) { menu.hidden = true; abtn.setAttribute("aria-expanded", "false"); } });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") { menu.hidden = true; abtn.setAttribute("aria-expanded", "false"); } });
    menu.addEventListener("click", function (e) {
      var b = e.target.closest("button"); if (!b) return;
      if (b.id === "fminus") prefs.scale = Math.max(0.8, Math.round((prefs.scale - 0.1) * 10) / 10);
      else if (b.id === "fplus") prefs.scale = Math.min(1.6, Math.round((prefs.scale + 0.1) * 10) / 10);
      else if (b.id === "sw-acc") { prefs.accents = !prefs.accents; applyAccents(); }
      savePrefs(); syncMenu();
    });
  }
  // accents and breathings: strip them from the text nodes, keeping the originals to restore
  var originals = null;
  function applyAccents() {
    if (prefs.accents && !originals) return;
    if (!originals) {
      originals = [];
      var w = document.createTreeWalker(reading, NodeFilter.SHOW_TEXT, null), t;
      while ((t = w.nextNode())) { if (/[Ͱ-Ͽἀ-῿]/.test(t.nodeValue)) originals.push([t, t.nodeValue]); }
    }
    originals.forEach(function (pair) { pair[0].nodeValue = prefs.accents ? pair[1] : bare(pair[1]); });
  }
  function bare(t) { return t.normalize("NFD").replace(/[̀́̂̓̔͂̈]/g, "").normalize("NFC"); }

  /* ---------- transliteration (scholarly scheme) ---------- */
  var B = { "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "ē", "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o", "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y", "φ": "ph", "χ": "ch", "ψ": "ps", "ω": "ō" };
  function trWord(w) {
    var L = Array.from(w).map(function (ch) { var d = ch.normalize("NFD"), b = d[0], l = b.toLowerCase(); return { b: l, up: b !== l, rough: d.indexOf("̔") >= 0, isub: d.indexOf("ͅ") >= 0, diaer: d.indexOf("̈") >= 0, raw: ch }; });
    var out = "", i = 0, cap = L.length && L[0].up, rough = L.slice(0, 2).some(function (x) { return x.rough; });
    while (i < L.length) {
      var x = L[i], b = x.b;
      if (!(b in B)) { out += (x.raw === "᾽" || x.raw === "’" || x.raw === "ʼ") ? "'" : x.raw; i++; continue; }
      var nx = L[i + 1] ? L[i + 1].b : "", nd = L[i + 1] ? L[i + 1].diaer : false;
      if ("αεηο".indexOf(b) >= 0 && (nx === "υ" || nx === "ι") && !nd) { out += B[b] + (nx === "υ" ? "u" : "i"); i += 2; }
      else if (b === "υ" && nx === "ι" && !nd) { out += "yi"; i += 2; }
      else if (b === "γ" && nx && "γκξχ".indexOf(nx) >= 0) { out += "n"; i++; }
      else if (b === "ρ" && i === 0) { out += "rh"; i++; }
      else { out += B[b] + (x.isub ? "i" : ""); i++; }
    }
    if (rough) out = "h" + out;
    if (cap) out = out[0].toUpperCase() + out.slice(1);
    return out;
  }
  function translit(t) { return t.replace(/[Ͱ-Ͽἀ-῿]+[᾽’ʼ]?/g, trWord).replace(/[··]/g, ";"); }

  /* ---------- Resources panel ---------- */
  var panel = $("rpanel"), pbody = $("rp-body");
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function plainText(p) {
    var c = p.cloneNode(true);
    Array.prototype.forEach.call(c.querySelectorAll(".spk,.steph,.pmark,.ref,.sr"), function (x) { x.remove(); });
    return c.textContent.replace(/\s+/g, " ").trim();
  }
  function select(p) {
    if (selected) selected.classList.remove("sel");
    if (selected === p || !p) { selected = null; panel.hidden = true; body.classList.remove("has-panel"); updateRef(); return; }
    selected = p; p.classList.add("sel");
    var sec = startOf.get(p) || "";
    var spk = p.querySelector(".spk");
    var greek = plainText(p);
    var scaife = urn ? "https://scaife.perseus.org/reader/" + urn + (sec ? ":" + sec : "") + "/" : "";
    pbody.innerHTML =
      '<div class="rp-ref">' + esc(title) + " " + esc(sec) + (spk ? ' <span class="rp-spk">· ' + esc(spk.textContent.trim()) + "</span>" : "") + "</div>"
      + '<h3>Transliteration</h3><div class="rp-item rp-tr">' + esc(translit(prefs.accents ? greek : greek)) + '<small>Scholarly scheme: η = ē, ω = ō, θ = th, φ = ph, χ = ch, ψ = ps, υ = y (u in diphthongs); rough breathing = h.</small></div>'
      + '<h3>About this text</h3><div class="rp-item"><a href="#contents">Contents and the story of this dialogue</a></div>'
      + (scaife ? '<h3>Source</h3><div class="rp-item"><a href="' + esc(scaife) + '">Open ' + esc(sec || "this text") + " in the Scaife Viewer (Perseus)</a></div>" : "");
    panel.hidden = false; body.classList.add("has-panel");
    try { history.replaceState(null, "", "#" + (p.querySelector(".steph") && !textBefore(p, p.querySelector(".steph")) ? p.querySelector(".steph").id : (location.hash.slice(1) || "text"))); } catch (e) {}
    updateRef();
  }
  reading.addEventListener("click", function (e) {
    if (e.target.closest("a")) return;
    if (window.getSelection && String(window.getSelection()).length) return;
    var p = e.target.closest("p"); if (p && reading.contains(p)) select(p);
  });
  reading.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" && e.key !== " ") return;
    var p = e.target.closest("p"); if (p && e.target === p) { e.preventDefault(); select(p); }
  });
  var pclose = $("rp-close"); if (pclose) pclose.addEventListener("click", function () { select(null); });

  /* ---------- start ---------- */
  doc.classList.add("js");
  syncMenu();
  if (!prefs.accents) applyAccents();
  setBarHeights();
  route();
})();
