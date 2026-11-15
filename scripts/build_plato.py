#!/usr/bin/env python3
"""Build the static Greek Plato corpus for the Sefarium site.

Reads Burnet's Oxford text from the PerseusDL canonical-greekLit TEI
(author tlg0059, Greek editions only) and writes one HTML page per work
plus a library index. No English translation is included.

    python3 scripts/build_plato.py
    python3 scripts/build_plato.py --cache /tmp/plato --out plato

The source commit is pinned so a rebuild sees the same text.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

from plato_catalogue import about_info, write_catalog_pages

SOURCE_COMMIT = "dacb04909e43dc47738828d33cc3d2b0635bc54c"
SOURCE_REPO = "PerseusDL/canonical-greekLit"
RAW = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/data/tlg0059"
TEI = "http://www.tei-c.org/ns/1.0"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
GREEK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")
SECTION_RE = re.compile(r"\d+[a-e]\Z")

# Thrasyllan order is the TLG order tlg001–tlg036. English titles are the
# names used on the library page; the Greek title is read from the CTS file.
WORKS = [
    ("001", "euthyphro", "Euthyphro", False),
    ("002", "apology", "Apology", False),
    ("003", "crito", "Crito", False),
    ("004", "phaedo", "Phaedo", False),
    ("005", "cratylus", "Cratylus", False),
    ("006", "theaetetus", "Theaetetus", False),
    ("007", "sophist", "Sophist", False),
    ("008", "statesman", "Statesman", False),
    ("009", "parmenides", "Parmenides", False),
    ("010", "philebus", "Philebus", False),
    ("011", "symposium", "Symposium", False),
    ("012", "phaedrus", "Phaedrus", False),
    ("013", "alcibiades-1", "Alcibiades I", False),
    ("014", "alcibiades-2", "Alcibiades II", True),
    ("015", "hipparchus", "Hipparchus", True),
    ("016", "lovers", "Lovers", True),
    ("017", "theages", "Theages", True),
    ("018", "charmides", "Charmides", False),
    ("019", "laches", "Laches", False),
    ("020", "lysis", "Lysis", False),
    ("021", "euthydemus", "Euthydemus", False),
    ("022", "protagoras", "Protagoras", False),
    ("023", "gorgias", "Gorgias", False),
    ("024", "meno", "Meno", False),
    ("025", "hippias-major", "Hippias Major", False),
    ("026", "hippias-minor", "Hippias Minor", False),
    ("027", "ion", "Ion", False),
    ("028", "menexenus", "Menexenus", False),
    ("029", "cleitophon", "Cleitophon", True),
    ("030", "republic", "Republic", False),
    ("031", "timaeus", "Timaeus", False),
    ("032", "critias", "Critias", False),
    ("033", "minos", "Minos", True),
    ("034", "laws", "Laws", False),
    ("035", "epinomis", "Epinomis", True),
    ("036", "letters", "Letters", False),
]

TETRALOGIES = [
    ("I", "Εὐθύφρων, Ἀπολογία, Κρίτων, Φαίδων"),
    ("II", "Κρατύλος, Θεαίτητος, Σοφιστής, Πολιτικός"),
    ("III", "Παρμενίδης, Φίληβος, Συμπόσιον, Φαῖδρος"),
    ("IV", "Ἀλκιβιάδης, Ἵππαρχος, Ἐρασταί"),
    ("V", "Θεάγης, Χαρμίδης, Λάχης, Λύσις"),
    ("VI", "Εὐθύδημος, Πρωταγόρας, Γοργίας, Μένων"),
    ("VII", "Ἱππίας, Ἴων, Μενέξενος"),
    ("VIII", "Κλειτοφῶν, Πολιτεία, Τίμαιος, Κριτίας"),
    ("IX", "Μίνως, Νόμοι, Ἐπινομίς, Ἐπιστολαί"),
]

GREEK_NUM = {
    1: "αʹ", 2: "βʹ", 3: "γʹ", 4: "δʹ", 5: "εʹ", 6: "ϛʹ",
    7: "ζʹ", 8: "ηʹ", 9: "θʹ", 10: "ιʹ", 11: "ιαʹ", 12: "ιβʹ", 13: "ιγʹ",
}

# Phrases that must survive into the HTML, taken from the Burnet text.
SPOT = {
    "apology": [
        "ὅτι μὲν ὑμεῖς, ὦ ἄνδρες Ἀθηναῖοι",
        "ὁ δὲ ἀνεξέταστος βίος οὐ βιωτὸς ἀνθρώπῳ",
        "ἄδηλον παντὶ πλὴν ἢ τῷ θεῷ",
    ],
    "symposium": [
        "δοκῶ μοι περὶ ὧν πυνθάνεσθε",
        "οἴκοι ἀναπαύεσθαι",
    ],
    "republic": [
        "κατέβην χθὲς εἰς Πειραιᾶ",
        "ὁπότε γὰρ τὸ δίκαιον μὴ οἶδα ὅ ἐστιν",
        "ἐγὼ μὲν οὖν ταῦτα εἰπὼν ᾤμην λόγου ἀπηλλάχθαι",
    ],
}


def local(tag: str) -> str:
    return tag.split("}", 1)[-1] if isinstance(tag, str) else tag


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def greek_num(n: str) -> str:
    return GREEK_NUM.get(int(n), n)


def fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    req = urllib.request.Request(url, headers={"User-Agent": "sefarium-plato-build"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())


def ensure_sources(cache: Path) -> None:
    for num, _slug, _en, _dub in WORKS:
        work = cache / f"tlg{num}"
        fetch(f"{RAW}/tlg{num}/__cts__.xml", work / "__cts__.xml")
        cts = (work / "__cts__.xml").read_text(encoding="utf-8")
        urns = re.findall(
            rf'urn="(urn:cts:greekLit:tlg0059\.tlg{num}\.perseus-grc\d)"', cts
        )
        if not urns:
            raise SystemExit(f"no Greek edition listed for tlg{num}")
        urn = sorted(urns)[-1]
        suffix = urn.rsplit("perseus-", 1)[-1]
        name = f"tlg0059.tlg{num}.perseus-{suffix}.xml"
        fetch(f"{RAW}/tlg{num}/{name}", work / name)


def parse_cts(path: Path) -> dict:
    root = ET.parse(path).getroot()
    eng, grc, burnet = [], None, None
    for el in root.iter():
        tag = local(el.tag)
        lang = el.get(XML_LANG) or ""
        if tag == "title" and lang in ("eng", "en"):
            text = nfc("".join(el.itertext()).strip())
            if text:
                eng.append(text)
        elif tag == "label" and lang == "grc" and grc is None:
            grc = nfc("".join(el.itertext()).strip())
        elif tag == "description" and burnet is None:
            text = " ".join("".join(el.itertext()).split())
            if "Burnet" in text:
                burnet = text
    if not grc or not burnet:
        raise SystemExit(f"missing Greek label or Burnet description in {path}")
    vol = re.search(r"Tomus\s+([IVXLC]+)", burnet)
    # The CTS record names Burnet with his life dates ("1863-1928"); the
    # publication year is the one after the publisher.
    year = re.search(r"Press,?\s*(1[89]\d{2}|20\d{2})", burnet)
    edition = "John Burnet, Platonis Opera (Oxford: Clarendon Press"
    edition += f", {year.group(1)}" if year else ""
    edition += ")"
    if vol:
        edition += f", vol. {vol.group(1)}"
    return {"greek": grc, "english_cts": eng, "edition": edition, "burnet": burnet}


def greek_chars(text: str) -> int:
    return len(GREEK_RE.findall(text))


class Renderer:
    def __init__(self) -> None:
        self.blocks: list[str] = []
        self.buf: list[str] = []
        self.pending: list[tuple[object, list[str]]] = []
        self.in_named_said = 0
        self.ids: set[str] = set()
        self.sections: list[str] = []
        self.pages: list[str] = []
        self.page_ids: list[tuple[str, str]] = []
        self.toc: list[tuple[str, str, str]] = []
        self.speakers: list[str] = []
        self.unknown: set[str] = set()
        self.qdepth = 0

    def unique(self, base: str) -> str:
        if base not in self.ids:
            self.ids.add(base)
            return base
        n = 2
        while f"{base}-{n}" in self.ids:
            n += 1
        ident = f"{base}-{n}"
        self.ids.add(ident)
        return ident

    def has_words(self) -> bool:
        html_so_far = "".join(self.buf)
        html_so_far = re.sub(r'<span class="spk\b[^>]*>.*?</span>', "", html_so_far)
        plain = re.sub(r"<[^>]+>", "", html_so_far)
        return bool(GREEK_RE.search(plain))

    def flush(self) -> None:
        if not self.has_words():
            return
        text = cleanup("".join(self.buf)).strip()
        self.buf = []
        if text and GREEK_RE.search(re.sub(r"<[^>]+>", "", text)):
            self.blocks.append(f"<p>{text}</p>")

    def finish(self) -> None:
        self.flush()
        if self.buf:
            text = cleanup("".join(self.buf)).strip()
            self.buf = []
            if text:
                self.blocks.append(f"<p>{text}</p>")

    def add_text(self, raw: str) -> None:
        if raw is None:
            return
        text = nfc(raw).replace("\u00a0", " ").replace("\r", "")
        text = re.sub(r"[ \t]*\n[ \t]*", " ", text)
        text = re.sub(r"[ \t]+", " ", text)
        if not text:
            return
        if GREEK_RE.search(text):
            self.emit_speakers()
        self.buf.append(esc(text))

    def emit_speakers(self) -> None:
        if not self.pending:
            return
        names: list[str] = []
        for _token, group in self.pending:
            for name in group:
                if name not in names:
                    names.append(name)
                if name not in self.speakers:
                    self.speakers.append(name)
        self.pending.clear()
        self.buf.append(f'<span class="spk">{esc(", ".join(names))}</span> ')

    def page(self, n: str) -> None:
        self.pages.append(n)
        ident = self.unique("p" + n)
        self.page_ids.append((n, ident))
        if self.has_words():
            self.buf.append(
                f'<span class="pmark" id="{ident}" title="Stephanus page {esc(n)}">{esc(n)}</span> '
            )
            return
        pending = self.buf[:]
        self.buf = []
        self.blocks.append(
            f'<div class="page-head" id="{ident}" role="doc-pagebreak" '
            f'aria-label="Stephanus page {esc(n)}">'
            f'<span class="sr">Stephanus page </span>{esc(n)}</div>'
        )
        self.buf = pending

    def section(self, n: str) -> None:
        if n == "imbedded dialogue":
            self.flush()
            self.blocks.append(
                '<h2 class="divhead" id="embedded">'
                '<span class="gk">ὁ διάλογος</span> '
                '<span class="en">the dialogue, read aloud</span></h2>'
            )
            self.toc.append(("embedded", "embedded", "The dialogue"))
            return
        if not SECTION_RE.fullmatch(n or ""):
            return
        self.sections.append(n)
        ident = self.unique("s" + n)
        self.buf.append(
            f'<a class="steph" id="{ident}" href="#{ident}" '
            f'title="Stephanus {esc(n)}">{esc(n)}</a> '
        )

    def speech(self, n: str) -> None:
        self.flush()
        label = {"1": "αʹ", "2": "βʹ", "3": "γʹ"}.get(n, n)
        english = {"1": "First speech", "2": "Second speech", "3": "Third speech"}.get(n, "Speech")
        ident = f"speech-{n}"
        self.blocks.append(
            f'<h2 class="divhead" id="{ident}">'
            f'<span class="gk">λόγος {label}</span> '
            f'<span class="en">{english}</span></h2>'
        )
        self.toc.append((ident, ident, english))

    def walk(self, el: ET.Element) -> None:
        tag = local(el.tag)
        handler = {
            "p": self.handle_p,
            "div": self.handle_div,
            "said": self.handle_said,
            "milestone": self.handle_milestone,
            "label": self.handle_label,
            "q": self.handle_q,
            "quote": self.handle_quote,
            "l": self.handle_l,
            "bibl": self.handle_bibl,
            "cit": self.handle_children,
            "add": self.handle_add,
            "del": self.handle_del,
            "gap": self.handle_gap,
            "emph": self.handle_em,
            "head": self.handle_skip,
            "note": self.handle_skip,
        }.get(tag)
        if handler:
            handler(el)
        else:
            if tag not in {
                "body", "persName", "placeName", "name", "rs", "term", "sic",
                "corr", "foreign", "w", "seg", "num", "title", "hi", "abbr",
                "expan", "orig", "reg", "unclear", "supplied", "surplus",
            }:
                self.unknown.add(tag)
            self.handle_children(el)

    def handle_children(self, el: ET.Element) -> None:
        if el.text:
            self.add_text(el.text)
        for child in list(el):
            self.walk(child)
            if child.tail:
                self.add_text(child.tail)

    def handle_skip(self, el: ET.Element) -> None:
        return

    def handle_p(self, el: ET.Element) -> None:
        self.flush()
        self.handle_children(el)
        self.flush()

    def handle_div(self, el: ET.Element) -> None:
        subtype = el.get("subtype")
        n = el.get("n") or ""
        if subtype == "book":
            self.flush()
            ident = f"book-{n}"
            self.blocks.append(
                f'<h2 class="divhead" id="{ident}">Βιβλίον {greek_num(n)} '
                f'<span class="en">Book {esc(n)}</span></h2>'
            )
            self.toc.append((ident, ident, f"Book {n}"))
            self.handle_children(el)
            self.flush()
            return
        if subtype == "letter":
            self.flush()
            ident = f"letter-{n}"
            self.blocks.append(
                f'<h2 class="divhead" id="{ident}">Ἐπιστολὴ {greek_num(n)} '
                f'<span class="en">Letter {esc(n)}</span></h2>'
            )
            self.toc.append((ident, ident, f"Letter {n}"))
            self.handle_children(el)
            self.flush()
            return
        self.handle_children(el)

    def handle_said(self, el: ET.Element) -> None:
        self.emit_speakers()
        who = el.get("who")
        show = bool(who) and el.get("rend") != "merge"
        token = object()
        if show:
            self.pending.append((token, parse_who(who)))
        if who:
            self.in_named_said += 1
        self.handle_children(el)
        if who:
            self.in_named_said -= 1
        self.pending = [item for item in self.pending if item[0] is not token]

    def handle_milestone(self, el: ET.Element) -> None:
        unit = el.get("unit") or ""
        n = el.get("n") or ""
        if unit == "page" and n:
            self.page(n)
        elif unit == "section":
            self.section(n)
        elif unit == "para":
            self.flush()
        elif unit == "speech" and n:
            self.speech(n)

    def handle_label(self, el: ET.Element) -> None:
        if self.in_named_said:
            return
        text = nfc("".join(el.itertext()).strip())
        if text:
            self.buf.append(f'<span class="spk">{esc(text)}</span> ')

    def handle_q(self, el: ET.Element) -> None:
        kind = el.get("type") or ""
        if kind in ("emph", "term"):
            self.buf.append("<em>")
            self.handle_children(el)
            self.buf.append("</em>")
            return
        self.qdepth += 1
        open_q, close_q = ("«", "»") if self.qdepth == 1 else ("“", "”")
        self.buf.append(open_q)
        self.handle_children(el)
        self.buf.append(close_q)
        self.qdepth -= 1

    def handle_quote(self, el: ET.Element) -> None:
        verse = el.get("type") == "verse" or any(local(c.tag) == "l" for c in el.iter())
        if not verse:
            self.handle_children(el)
            return
        # Name the speaker before the poem, not inside the first line.
        self.emit_speakers()
        self.buf.append('<span class="verse">')
        self.handle_children(el)
        self.buf.append("</span>")

    def handle_l(self, el: ET.Element) -> None:
        text = "".join(el.itertext()).strip()
        has_gap = any(local(child.tag) == "gap" for child in el.iter())
        if not text and not has_gap:
            return
        self.emit_speakers()
        self.buf.append('<span class="line">')
        self.handle_children(el)
        self.buf.append("</span>")

    def handle_bibl(self, el: ET.Element) -> None:
        label = (el.get("n") or "").strip()
        if not label:
            label = " ".join("".join(el.itertext()).split())
        if label:
            self.buf.append(f' <cite class="ref">{esc(nfc(label))}</cite>')

    def handle_add(self, el: ET.Element) -> None:
        if not "".join(el.itertext()).strip():
            return
        self.buf.append('<span class="ed add">⟨')
        self.handle_children(el)
        self.buf.append("⟩</span>")

    def handle_del(self, el: ET.Element) -> None:
        if not "".join(el.itertext()).strip():
            return
        self.buf.append('<span class="ed del">[')
        self.handle_children(el)
        self.buf.append("]</span>")

    def handle_gap(self, el: ET.Element) -> None:
        if el.get("reason") == "ellipsis":
            self.buf.append('<span class="gap" title="ellipsis">[…]</span>')
        else:
            self.buf.append('<span class="gap" title="lacuna">[***]</span>')

    def handle_em(self, el: ET.Element) -> None:
        self.buf.append("<em>")
        self.handle_children(el)
        self.buf.append("</em>")


def parse_who(who: str) -> list[str]:
    return [nfc(part.strip()) for part in re.findall(r"#([^#]+)", who or "") if part.strip()]


def cleanup(fragment: str) -> str:
    def fix(match: re.Match[str]) -> str:
        text = match.group(0)
        text = re.sub(r" +", " ", text)
        text = re.sub(r" +([.,;:··;])", r"\1", text)
        text = re.sub(r"« +", "«", text)
        text = re.sub(r" +»", "»", text)
        text = re.sub(r"“ +", "“", text)
        text = re.sub(r" +”", "”", text)
        text = re.sub(r"\[ +", "[", text)
        text = re.sub(r" +\]", "]", text)
        text = re.sub(r"⟨ +", "⟨", text)
        text = re.sub(r" +⟩", "⟩", text)
        return text

    return re.sub(r"[^<]+", fix, fragment)


def xml_greek_baseline(path: Path) -> tuple[int, list[str], list[str]]:
    """Greek letters in the body, excluding speaker abbreviations and the title head."""
    root = ET.parse(path).getroot()
    body = next(el for el in root.iter() if local(el.tag) == "body")
    sections, pages = [], []
    skipped = 0
    for el in body.iter():
        tag = local(el.tag)
        if tag in ("label", "head"):
            skipped += greek_chars("".join(el.itertext()))
        elif tag == "milestone":
            unit, n = el.get("unit"), el.get("n") or ""
            if unit == "section" and SECTION_RE.fullmatch(n):
                sections.append(n)
            elif unit == "page" and n:
                pages.append(n)
    total = greek_chars("".join(body.itertext())) - skipped
    return total, sections, pages


def render_work(xml_path: Path) -> tuple[Renderer, int]:
    root = ET.parse(xml_path).getroot()
    body = next(el for el in root.iter() if local(el.tag) == "body")
    renderer = Renderer()
    renderer.walk(body)
    renderer.finish()
    if renderer.unknown:
        raise SystemExit(f"unhandled tags in {xml_path.name}: {sorted(renderer.unknown)}")
    return renderer, greek_chars("".join(body.itertext()))


def page_shell(title: str, body: str, current: str, extra: str = "") -> str:
    nav = [
        ("../index.html", "texts", "Texts"),
        ("../texts/plato.html", "plato", "Plato"),
        ("alcibiades-1-annotated.html#topics", "topics", "Topics"),
        ("alcibiades-1-annotated.html#donate", "donate", "Donate"),
    ]
    items = []
    for href, key, label in nav:
        current_attr = ' aria-current="page"' if key == current else ""
        items.append(f'<li><a href="{href}"{current_attr}>{label}</a></li>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="icon" href="../favicon.ico" sizes="any">
<link rel="icon" href="../favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<link rel="license" href="https://creativecommons.org/licenses/by-sa/4.0/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Gentium+Book+Plus:ital,wght@0,400;0,700;1,400&amp;family=EB+Garamond:ital,wght@0,400;0,500;1,400&amp;family=Source+Sans+3:wght@400;600&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="plato.css">
<script>document.documentElement.classList.add("js");</script>
</head>
<body{extra}>
<a class="skip" href="#text">Skip to text</a>
<nav class="sitebar" aria-label="Site">
  <a class="brand" href="../index.html"><span class="mark" aria-hidden="true">Ψ</span>Sefarium</a>
  <ul>
    {''.join(items)}
  </ul>
</nav>
{body}
</body>
</html>
"""


def credits_block(urn: str, filename: str, edition: str) -> str:
    # filename is tlg0059.tlg002.perseus-grc2.xml; the work directory is tlg002.
    work = filename.split(".")[1]
    github = (
        f"https://github.com/{SOURCE_REPO}/blob/{SOURCE_COMMIT}/data/tlg0059/"
        f"{work}/{filename}"
    )
    scaife = f"https://scaife.perseus.org/reader/{urn}/"
    return f"""<footer class="credits">
  <p>Greek text: {esc(edition)}. Digital text from the <a href="https://www.perseus.tufts.edu/">Perseus Digital Library</a>, Tufts University (<a href="{esc(github)}">{esc(urn)}</a>).</p>
  <p>Licence: <a href="https://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0</a>. Reuse must credit the Perseus Digital Library, Tufts University, and link to <a href="https://www.perseus.tufts.edu/">perseus.tufts.edu</a>. <a href="{esc(scaife)}">Open this text in the Scaife Viewer</a>.</p>
  <p><a href="../texts/plato.html">All dialogues</a> · <a href="../index.html">Sefarium</a></p>
</footer>"""


# Words missing from the pinned Perseus TEI, checked against the Perseus Hopper
# text of the same Burnet edition. Each entry: slug -> [(text before, inserted)].
# Inserted text goes immediately after the "before" text, which must occur once.
RESTORED = {
    # 104a: the line before the 104b milestone is dropped in perseus-grc2.
    "alcibiades-1": [("ἐν τῇ σεαυτοῦ ", "πόλει, οὔσῃ μεγίστῃ τῶν Ἑλληνίδων, καὶ ")],
}


def restore_missing(slug: str, page: str) -> str:
    for before, inserted in RESTORED.get(slug, []):
        if page.count(before) != 1:
            raise SystemExit(f"{slug}: cannot place restored text after {before!r}")
        if inserted not in page:
            page = page.replace(before, before + inserted, 1)
    return page


def work_page(meta: dict, renderer: Renderer, prev_m: dict | None, next_m: dict | None) -> str:
    """A dialogue page in two views, as on Sefaria: contents, then the reader."""
    greek = meta["greek"]
    english = meta["english"]
    slug = meta["slug"]
    info = about_info(slug)
    first = renderer.sections[0] if renderer.sections else ""
    last = renderer.sections[-1] if renderer.sections else ""
    span = f"{first}–{last}" if first else ""
    start = f"#s{first}" if first else "#text"
    persons = ""
    if len(renderer.speakers) >= 2:
        persons = (
            '<h3>Persons of the dialogue</h3>'
            f'<p class="gk" lang="grc">{" · ".join(esc(name) for name in renderer.speakers)}</p>'
        )
    note = ""
    if meta["num"] == "016":
        note = (
            '<p class="note">Speaker changes are not marked in the Perseus TEI of this dialogue. '
            "The Greek is complete; the turns stay in the narrator’s voice, as in the source.</p>"
        )
    elif meta["num"] == "013":
        note = (
            '<p class="note">Also read in Sefarium with a new English translation and commentary: '
            '<a href="alcibiades-1-annotated.html">Alcibiades I, annotated</a>.</p>'
        )
    divisions = ""
    if renderer.toc:
        kind = "Book" if renderer.toc[0][0].startswith("book") else (
            "Letter" if renderer.toc[0][0].startswith("letter") else "Part")
        def short(label: str) -> str:
            m = re.search(r"(\d+)\s*$", label)
            return m.group(1) if m else label
        cells = "".join(
            f'<a class="cell" href="#{esc(ident)}" title="{esc(label)}">{esc(short(label))}</a>'
            for ident, _href, label in renderer.toc
        )
        divisions = f'<h3 class="gridlabel">{kind}</h3><div class="grid">{cells}</div>'
    pages = "".join(
        f'<a class="cell" href="#{esc(ident)}">{esc(n)}</a>' for n, ident in renderer.page_ids
    )
    contents = f"""{divisions}<h3 class="gridlabel">Stephanus page</h3><div class="grid">{pages}</div>"""
    neighbours = []
    if prev_m:
        neighbours.append(f'<a href="{prev_m["slug"]}.html" rel="prev"><span class="dir">Previous</span>{esc(prev_m["english"])} <span class="gk" lang="grc">{esc(prev_m["greek"])}</span></a>')
    if next_m:
        neighbours.append(f'<a href="{next_m["slug"]}.html" rel="next"><span class="dir">Next</span>{esc(next_m["english"])} <span class="gk" lang="grc">{esc(next_m["greek"])}</span></a>')
    pager = f'<nav class="pager" aria-label="Works">{"".join(neighbours)}</nav>'
    urn = meta["urn"]
    body = f"""<div class="toc-view" id="contents">
  <main class="toc-main">
    <h1 class="toc-title">{esc(english)} <span class="gk" lang="grc">{esc(greek)}</span></h1>
    <p class="toc-cat"><a href="../texts/plato.html">Plato</a> · Tetralogy {esc(meta["tetralogy"])} · {esc(span)}</p>
    <p class="toc-short">{esc(info["short"])}</p>
    <a class="btn" href="{start}">Start Reading</a>
    {note}
    <div class="tabs" role="presentation"><span class="tab on">Contents</span></div>
    {contents}
  </main>
  <aside class="toc-about" aria-label="About this text">
    <h2>About This Text</h2>
    <p class="kv"><b>Dramatic date</b> {esc(info["when"])}</p>
    <p>{esc(info["story"])}</p>
    <h3>Love in this dialogue</h3>
    <p>{esc(info["love"])}</p>
    {persons}
    <h3>Greek text</h3>
    <p>{esc(meta["edition"])}. Digital text from the <a href="https://www.perseus.tufts.edu/">Perseus Digital Library</a>, Tufts University.</p>
    {pager}
  </aside>
</div>
<div class="reader-view" id="text">
  <div class="rbar">
    <a class="rb-back" href="#contents" aria-label="Contents of {esc(english)}" title="Contents">☰</a>
    <a class="rb-title" href="#contents" title="Contents"><span class="t">{esc(english)}</span> <span class="ref" id="rb-ref">{esc(first)}</span><small>Burnet, Oxford · Greek</small></a>
    <button class="rb-a" id="rb-a" aria-haspopup="true" aria-expanded="false" aria-controls="rmenu" title="Text display options">A</button>
    <div class="rmenu" id="rmenu" hidden role="dialog" aria-label="Text display options">
      <div class="row"><span>Font size</span><span class="size"><button id="fminus" aria-label="Smaller text">−</button><button id="fplus" aria-label="Larger text">+</button></span></div>
      <div class="row"><span>Accents &amp; breathings</span><button class="switch" role="switch" id="sw-acc" aria-checked="true" aria-label="Accents and breathings"></button></div>
    </div>
  </div>
  <div class="rwork">
    <div class="rcol">
      <article class="reading" lang="grc">
        {''.join(renderer.blocks)}
      </article>
      {pager}
      {credits_block(urn, meta["filename"], meta["edition"])}
    </div>
    <aside class="rpanel" id="rpanel" hidden aria-label="Resources">
      <header><span>Resources</span><button id="rp-close" aria-label="Close resources">✕</button></header>
      <div id="rp-body"></div>
    </aside>
  </div>
</div>
<script src="reader.js"></script>"""
    return page_shell(f"{greek} · {english} · Sefarium", body, "plato",
                      extra=f' data-title="{esc(english)}" data-urn="{esc(urn)}" class="work-page v-contents"')


def check(works: list[dict], out: Path) -> None:
    errors: list[str] = []
    index = (out.parent / "texts" / "plato.html").read_text(encoding="utf-8")
    if index.count("<li><a href=") < 36:
        # site nav also has links; count work rows instead
        pass
    if "Πλάτων" not in index or "Perseus Digital Library" not in index:
        errors.append("index missing title or attribution")
    if "creativecommons.org/licenses/by-sa/4.0" not in index:
        errors.append("index missing licence link")
    for meta in works:
        href = f'{meta["slug"]}.html'
        if f'href="../plato/{href}"' not in index:
            errors.append(f"index does not link to {href}")
        page = (out / href).read_text(encoding="utf-8")
        for needle in (
            "Perseus Digital Library",
            "Tufts",
            "Burnet",
            "creativecommons.org/licenses/by-sa/4.0",
            meta["greek"],
            meta["urn"],
        ):
            if needle not in page:
                errors.append(f'{href} missing {needle!r}')
        if "Clarendon Press, 1863" in page:
            errors.append(f"{href} prints Burnet's birth year as the publication year")
        if "\ufffd" in page or "Ã" in page or "Î" in page:
            errors.append(f"{href} has encoding damage")
        steph = len(re.findall(r'class="steph"', page))
        if steph != len(meta["sections"]):
            errors.append(
                f'{href} stephanus anchors {steph} != source sections {len(meta["sections"])}'
            )
        ratio = meta["html_greek"] / meta["xml_greek"] if meta["xml_greek"] else 0
        if ratio < 0.97:
            errors.append(f'{href} keeps only {ratio:.1%} of the Greek letters')
        for phrase in SPOT.get(meta["slug"], []):
            if phrase not in page:
                errors.append(f'{href} missing spot phrase {phrase!r}')
    for slug, fixes in RESTORED.items():
        page = (out / f"{slug}.html").read_text(encoding="utf-8")
        for _before, inserted in fixes:
            if inserted not in page:
                errors.append(f"{slug}.html is missing restored text {inserted!r}")
    apology = (out / "apology.html").read_text(encoding="utf-8")
    if 'id="s17a"' not in apology or 'id="s42a"' not in apology:
        errors.append("apology missing 17a or 42a")
    if 'id="speech-2"' not in apology or 'id="speech-3"' not in apology:
        errors.append("apology missing the later speeches")
    republic = (out / "republic.html").read_text(encoding="utf-8")
    for n in range(1, 11):
        if f'id="book-{n}"' not in republic:
            errors.append(f"republic missing book {n}")
    book1, book2, end = republic.find('id="book-1"'), republic.find('id="book-2"'), republic.find('id="book-10"')
    if not (0 <= book1 < republic.find("κατέβην χθὲς εἰς Πειραιᾶ") < book2 < republic.find("ἐγὼ μὲν οὖν ταῦτα εἰπὼν") < end):
        errors.append("republic book boundaries are out of order")
    if 'id="s327a"' not in republic or 'id="s354c"' not in republic or 'id="s621d"' not in republic:
        errors.append("republic missing 327a, 354c, or 621d")
    symposium = (out / "symposium.html").read_text(encoding="utf-8")
    if 'id="s172a"' not in symposium or 'id="s223d"' not in symposium:
        errors.append("symposium missing 172a or 223d")
    if symposium.find("δοκῶ μοι περὶ ὧν πυνθάνεσθε") > symposium.find("οἴκοι ἀναπαύεσθαι"):
        errors.append("symposium ending precedes its opening")
    if '<span class="spk">Ἀπολλόδωρος</span>' not in symposium:
        errors.append("symposium does not name Apollodorus")
    euthyphro = (out / "euthyphro.html").read_text(encoding="utf-8")
    if '<span class="spk">Εὐθύφρων</span>' not in euthyphro or '<span class="spk">Σωκράτης</span>' not in euthyphro:
        errors.append("euthyphro missing speaker names")
    laws = (out / "laws.html").read_text(encoding="utf-8")
    if sum(1 for n in range(1, 13) if f'id="book-{n}"' in laws) != 12:
        errors.append("laws does not have 12 books")
    letters = (out / "letters.html").read_text(encoding="utf-8")
    if sum(1 for n in range(1, 14) if f'id="letter-{n}"' in letters) != 13:
        errors.append("letters does not have 13 letters")
    parmenides = (out / "parmenides.html").read_text(encoding="utf-8")
    # The frame narrator is marked; the inner dialectic is not given speaker names.
    if parmenides.count('<span class="spk">') > 5:
        errors.append("parmenides invented speaker names for the unmarked dialectic")
    if "εἶεν δή" not in parmenides or "πῶς γὰρ ἄν" not in parmenides:
        errors.append("parmenides dialectic missing")
    if errors:
        raise SystemExit("verification failed:\n- " + "\n- ".join(errors))
    print(f"verified {len(works)} works")


def build(cache: Path, out: Path) -> None:
    ensure_sources(cache)
    out.mkdir(parents=True, exist_ok=True)
    built: list[dict] = []
    for index, (num, slug, english, dubium) in enumerate(WORKS):
        work_dir = cache / f"tlg{num}"
        cts = parse_cts(work_dir / "__cts__.xml")
        xmls = sorted(path for path in work_dir.glob("tlg0059*.xml"))
        if len(xmls) != 1:
            raise SystemExit(f"expected one Greek XML for tlg{num}, found {xmls}")
        xml_path = xmls[0]
        baseline, sections, pages = xml_greek_baseline(xml_path)
        renderer, _all = render_work(xml_path)
        suffix = xml_path.name.split("perseus-", 1)[1].replace(".xml", "")
        urn = f"urn:cts:greekLit:tlg0059.tlg{num}.perseus-{suffix}"
        meta = {
            "num": num,
            "slug": slug,
            "english": english,
            "greek": cts["greek"],
            "edition": cts["edition"],
            "dubium": dubium,
            "tetralogy": TETRALOGIES[index // 4][0],
            "urn": urn,
            "filename": xml_path.name,
            "sections": sections,
            "pages": pages,
            "span": f"{sections[0]}–{sections[-1]}" if sections else "",
            "xml_greek": baseline,
            "html_greek": greek_chars("".join(renderer.blocks)),
        }
        if cts["english_cts"] and not any(english.split()[0] in title or title.split()[0] in english for title in cts["english_cts"]):
            print(f"warning: {num} display title {english!r} not in CTS {cts['english_cts']}")
        built.append(meta)
        print(
            f'{num} {slug:16} {meta["span"]:12} sections {len(sections):4} '
            f'speakers {len(renderer.speakers):2} greek {meta["html_greek"]/baseline:.1%}'
        )
        # stash renderer on the meta only until the page is written
        meta["_renderer"] = renderer

    for index, meta in enumerate(built):
        prev_m = built[index - 1] if index else None
        next_m = built[index + 1] if index + 1 < len(built) else None
        page = restore_missing(meta["slug"], work_page(meta, meta.pop("_renderer"), prev_m, next_m))
        (out / f'{meta["slug"]}.html').write_text(page, encoding="utf-8")
    greeks = {meta["slug"]: meta["greek"] for meta in built}
    write_catalog_pages(out.parent, greeks)
    check(built, out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path("/tmp/plato"))
    parser.add_argument("--out", type=Path, default=Path("plato"))
    args = parser.parse_args()
    build(args.cache, args.out)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
