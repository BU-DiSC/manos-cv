#!/usr/bin/env python3
"""Render the LaTeX CV (cv.tex + sections/*.tex) as a standalone HTML page.

Only the semantic macros defined in athcv.sty are understood; that is the
contract that keeps the PDF and the web page in sync. Standard library only.

Usage: python3 tools/build_html.py [OUTDIR]     (default: site/)
"""
import datetime
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_NAME = "ManosAthanassoulisCV-EN.pdf"

# ----------------------------------------------------------------- parsing --

def strip_comments(src):
    out = []
    for line in src.splitlines():
        m = re.search(r"(?<!\\)%", line)
        out.append(line[: m.start()] if m else line)
    return "\n".join(out)


def read_group(s, i):
    """s[i] == '{' -> (content, index after matching '}')."""
    assert s[i] == "{", (s[i:i + 40])
    depth, j = 0, i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError("unbalanced braces near: " + s[i:i + 60])


def skip_ws(s, i):
    while i < len(s) and s[i] in " \t\n":
        i += 1
    return i


def read_args(s, i, n):
    args = []
    for _ in range(n):
        i = skip_ws(s, i)
        a, i = read_group(s, i)
        args.append(a)
    return args, i


# ------------------------------------------------------- inline LaTeX→HTML --

SIMPLE = {
    "textbf": ("<strong>", "</strong>"),
    "textit": ("<em>", "</em>"),
    "emph": ("<em>", "</em>"),
    "textmd": ("<span class=\"md\">", "</span>"),
    "adv": ("<u class=\"adv\">", "</u>"),
    "award": ("<em class=\"award\">", "</em>"),
    "awardbf": ("<strong class=\"award\">", "</strong>"),
    "awardrm": ("<span class=\"award\">", "</span>"),
    "textsuperscript": ("<sup>", "</sup>"),
    "uline": ("<u>", "</u>"),
}
ESCAPES = {"&": "&amp;", "%": "%", "$": "$", "#": "#", "_": "_", "{": "{", "}": "}",
           " ": " ", ",": "\u2009"}


def inline(s):
    """Convert an inline LaTeX fragment to HTML."""
    out, i = [], 0
    s = s.replace("``", "\u201c").replace("''", "\u201d").replace("---", "\u2014").replace("--", "\u2013")
    while i < len(s):
        c = s[i]
        if c == "\\":
            if i + 1 < len(s) and s[i + 1] == "\\":
                out.append("<br>")
                i += 2
                continue
            if i + 1 < len(s) and not s[i + 1].isalpha():
                out.append(ESCAPES.get(s[i + 1], html.escape(s[i + 1])))
                i += 2
                continue
            m = re.match(r"\\([A-Za-z]+)\*?", s[i:])
            name = m.group(1)
            i += m.end()
            if name == "me":
                out.append("<strong class=\"me\">M. Athanassoulis</strong>")
                if s[i:i + 2] == "{}":
                    i += 2
            elif name in SIMPLE:
                (arg,), i = read_args(s, i, 1)
                o, c2 = SIMPLE[name]
                out.append(o + inline(arg) + c2)
            elif name == "href":
                (url, text), i = read_args(s, i, 2)
                url = url.replace("\\%", "%").replace("\\#", "#").replace("\\_", "_")
                out.append("<a href=\"%s\">%s</a>" % (html.escape(url, quote=True), inline(text)))
            elif name in ("quad", "qquad"):
                out.append(" &emsp; ")
            elif name == "today":
                out.append(datetime.date.today().strftime("%B %Y"))
            else:  # unknown command: render its argument(s) plainly
                if i < len(s) and s[i] == "{":
                    (arg,), i = read_args(s, i, 1)
                    out.append(inline(arg))
        elif c == "{" or c == "}":
            i += 1
        elif c == "~":
            out.append("&nbsp;")
            i += 1
        else:
            j = i
            while j < len(s) and s[j] not in "\\{}~":
                j += 1
            out.append(html.escape(s[i:j], quote=False))
            i = j
    return re.sub(r"\s+", " ", "".join(out)).strip()


def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", inline(s)))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", plain(s).lower().replace("&", "and")).strip("-")


def parse_kv(body):
    """Parse 'key = {value}, key = {value}' (values may contain commas)."""
    kv, i = {}, 0
    while True:
        m = re.compile(r"\s*,?\s*([a-z]+)\s*=\s*").match(body, i)
        if not m:
            break
        i = m.end()
        if i < len(body) and body[i] == "{":
            v, i = read_group(body, i)
        else:
            j = body.find(",", i)
            j = len(body) if j < 0 else j
            v, i = body[i:j], j
        kv[m.group(1)] = v.strip()
    return kv


# ----------------------------------------------------- block macros → HTML --

ARITY = {"cvsection": 1, "cvsubsection": 1, "cvsubsubsection": 1, "cvpara": 1,
         "cventry": 1, "dated": 2, "membership": 2, "degree": 3, "job": 4,
         "phdgrad": 3, "teachinst": 1, "course": 2, "patent": 2,
         "pubcategory": 1, "paper": 1}


class Renderer:
    def __init__(self):
        self.sections = []      # (id, title, html)
        self.pubno = 0
        self.npubs = 0

    def render_file(self, path):
        src = strip_comments(open(path, encoding="utf-8").read())
        i, buf, title, sid = 0, [], None, None
        mode = None   # current wrapper: 'entries', 'dated', 'courses', 'papers'

        def close():
            nonlocal mode
            if mode == "papers":
                buf.append("</ol>")
            elif mode:
                buf.append("</div>")
            mode = None

        def open_(m, cls):
            nonlocal mode
            if mode != m:
                close()
                buf.append("<div class=\"%s\">" % cls)
                mode = m

        while i < len(src):
            i = skip_ws(src, i)
            if i >= len(src):
                break
            m = re.match(r"\\setlength\s*(\\[A-Za-z]+|\{[^}]*\})\s*\{[^}]*\}", src[i:])
            if m:
                i += m.end()
                continue
            if src.startswith("\\begin{papers}", i):
                close()
                buf.append("<ol class=\"pubs\" start=\"%d\">" % (self.pubno + 1))
                mode = "papers"
                i += len("\\begin{papers}")
                continue
            if src.startswith("\\end{papers}", i):
                close()
                i += len("\\end{papers}")
                continue
            m = re.match(r"\\([A-Za-z]+)", src[i:])
            if m and m.group(1) in ARITY:
                name = m.group(1)
                args, i = read_args(src, i + m.end(), ARITY[name])
                if name == "cvsection":
                    title, sid = args[0], slug(args[0])
                elif name == "cvsubsection":
                    close()
                    buf.append("<h3>%s</h3>" % inline(args[0]))
                elif name == "cvsubsubsection":
                    close()
                    buf.append("<h4>%s</h4>" % inline(args[0]))
                elif name == "pubcategory":
                    close()
                    buf.append("<h3>%s</h3>" % inline(args[0]))
                elif name == "cvpara":
                    close()
                    buf.append("<p>%s</p>" % inline(args[0]))
                elif name == "cventry":
                    open_("entries", "entries")
                    buf.append("<div class=\"entry\">%s</div>" % inline(args[0]))
                elif name in ("dated", "membership"):
                    open_("dated", "dated")
                    buf.append("<div class=\"when\">%s</div><div class=\"what\">%s</div>"
                               % (inline(args[0]), inline(args[1])))
                elif name == "job":
                    open_("jobs", "jobs")
                    buf.append("<div class=\"when\">%s</div><div class=\"what\"><strong>%s</strong> at "
                               "<strong>%s</strong></div><div class=\"where\">%s</div>"
                               % tuple(inline(a) for a in args))
                elif name == "degree":
                    close()
                    buf.append("<div class=\"degree\"><div class=\"deg-head\"><strong>%s</strong>"
                               "<strong class=\"inst\">%s</strong></div><div class=\"deg-detail\">%s</div></div>"
                               % (inline(args[0]), inline(args[1]), inline(args[2])))
                elif name == "phdgrad":
                    open_("entries", "entries")
                    buf.append("<div class=\"entry grad\"><div>%s</div><div class=\"sub\">Dissertation: "
                               "\u201c%s\u201d</div><div class=\"sub\">First position: %s</div></div>"
                               % tuple(inline(a) for a in args))
                elif name == "teachinst":
                    close()
                    buf.append("<h4 class=\"inst\">%s</h4>" % inline(args[0]))
                elif name == "course":
                    open_("courses", "courses")
                    buf.append("<div class=\"course\">%s</div><div class=\"terms\">%s</div>"
                               % (inline(args[0]), inline(args[1])))
                elif name == "patent":
                    close()
                    buf.append("<ul class=\"patents\"><li>\u201c%s\u201d, %s</li></ul>"
                               % (inline(args[0]), inline(args[1])))
                elif name == "paper":
                    if mode != "papers":
                        close()
                        buf.append("<ol class=\"pubs\" start=\"%d\">" % (self.pubno + 1))
                        mode = "papers"
                    buf.append(self.paper(parse_kv(args[0])))
                continue
            # free text up to the next blank line / block macro
            j = src.find("\n\n", i)
            nxt = re.search(r"\n\s*\\(%s|begin|end|setlength)\b" % "|".join(ARITY), src[i:])
            k = min(x for x in [j if j >= 0 else len(src), i + nxt.start() if nxt else len(src)])
            text = src[i:k].strip()
            if text:
                close()
                buf.append("<p class=\"note\">%s</p>" % inline(text))
            i = k
        close()
        if title is not None:
            self.sections.append((sid, plain(title), inline(title), "\n".join(buf)))

    def paper(self, kv):
        self.pubno += 1
        self.npubs += 1
        parts = ["%s, \u201c<span class=\"ptitle\">%s</span>\u201d, %s" % (
            inline(kv.get("authors", "")), inline(kv.get("title", "")), inline(kv.get("venue", "")))]
        if kv.get("year"):
            parts.append(", <strong>%s</strong>" % inline(kv["year"]))
        if kv.get("after"):
            parts.append(" " + inline(kv["after"]))
        parts.append(".")
        if kv.get("url"):
            url = kv["url"].replace("\\%", "%").replace("\\#", "#").replace("\\_", "_")
            parts.append(" <a class=\"plink\" href=\"%s\">link</a>" % html.escape(url, quote=True))
        if kv.get("note"):
            parts.append(" " + inline(kv["note"]))
        return "<li>%s</li>" % "".join(parts)


# ------------------------------------------------------------------- page --

def title_block(cv):
    m = re.search(r"\\cvtitle", cv)
    args, _ = read_args(cv, m.end(), 4)
    return args


def section_files(cv):
    return [os.path.join(ROOT, p + ".tex") for p in re.findall(r"^\s*\\input\{([^}]+)\}", cv, re.M)]


CSS = open(os.path.join(ROOT, "tools", "cv.css"), encoding="utf-8").read()


def build(outdir):
    cv = strip_comments(open(os.path.join(ROOT, "cv.tex"), encoding="utf-8").read())
    name, role, dept, contact = title_block(cv)
    r = Renderer()
    for f in section_files(cv):
        r.render_file(f)

    nav = "\n".join("<a href=\"#%s\">%s</a>" % (sid, html.escape(t)) for sid, t, _, _ in r.sections)
    body = "\n".join("<section id=\"%s\"><h2>%s</h2>\n%s\n</section>" % (sid, th, b)
                     for sid, _, th, b in r.sections)
    updated = datetime.date.today().strftime("%B %Y")
    has_pdf = os.path.exists(os.path.join(ROOT, PDF_NAME))
    pdf_btn = ("<a class=\"btn\" href=\"%s\" target=\"_blank\" rel=\"noopener\">View PDF</a>" % PDF_NAME) if has_pdf else ""

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{plain(name)} — Curriculum Vitae</title>
<meta name="description" content="Curriculum Vitae of {plain(name)}, {plain(role)}, {plain(dept)}.">
<script>
  // start in the browser's theme (light or dark), set before first paint
  document.documentElement.dataset.theme =
    window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>
<header class="masthead">
  <div class="wrap">
    <p class="kicker">Curriculum Vitae</p>
    <h1>{inline(name)}</h1>
    <p class="role">{inline(role)}</p>
    <p class="dept">{inline(dept)}</p>
    <p class="contact">{inline(contact)}</p>
    <p class="actions">{pdf_btn}<span class="stat">{r.npubs} publications</span><button class="theme-toggle" id="theme-toggle" type="button" aria-label="Toggle dark mode">Dark mode</button></p>
  </div>
</header>
<div class="wrap layout">
  <nav class="toc" aria-label="Sections">
    {nav}
  </nav>
  <main>
{body}
    <p class="updated">Last update: {updated}.</p>
  </main>
</div>
<script>
  (function () {{
    // two themes; the button offers the other one
    var btn = document.getElementById("theme-toggle"), root = document.documentElement;
    function show() {{
      var dark = root.dataset.theme === "dark";
      btn.textContent = dark ? "Light mode" : "Dark mode";
      btn.setAttribute("aria-pressed", dark ? "true" : "false");
    }}
    btn.addEventListener("click", function () {{
      root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
      show();
    }});
    show();
  }})();
</script>
</body>
</html>
"""
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    print("wrote %s (%d sections, %d publications)"
          % (os.path.join(outdir, "index.html"), len(r.sections), r.npubs))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "site"))
