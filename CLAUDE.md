# CV (LaTeX port of CV_EN_2026-11.docx)

Build: `make` (XeLaTeX via latexmk) → `ManosAthanassoulisCV-EN.pdf`, which is also copied to the parent folder (`../ManosAthanassoulisCV-EN.pdf`) on every build. Always build with `make` (not raw latexmk) so the copy happens. Must stay warning-free and visually match the Word original.

- `cv.tex`: title block and the section order (`\input{sections/...}`).
- `athcv.sty`: **all** look & feel (fonts, margins, spacing, header/footer, macros). Content files never contain raw formatting such as `\vspace`, `\hspace` or font sizes.
- `sections/*.tex`: one file per CV section, using only the macros below.
- `tools/build_html.py` + `tools/cv.css`: render the same sources as the web CV, published to GitHub Pages by `.github/workflows/pages.yml` on every push to `main`. If you add or change a macro in `athcv.sty`, mirror it in `build_html.py`. Check with `python3 tools/build_html.py` (→ `site/`, git-ignored).
- Git: repo `BU-DiSC/manos-cv`. The `.githooks/pre-commit` hook (enabled via `git config core.hooksPath .githooks`) rebuilds and stages the PDF whenever sources change. The PDF is committed because CI has no MS Garamond. `fonts/` holds local copies of MS Garamond and is git-ignored: it is not redistributable, so never commit it.

## Conventions when updating content
- Entries are **newest first** in every section. Insert new items at the top of their list or year.
- Publications are numbered automatically and the numbering continues across categories. Never type numbers.
- Use Unicode “curly quotes” and en dashes (–) the way the existing entries do.
- Escape `&`, `%`, `$`, `#` and `_` as `\&`, `\%`, `\$`, `\#` and `\_`. Inside `url = {...}` keep the URL raw, but escape `%` and `#`.
- The "Last update" date at the end is automatic (`\today`), so don't edit it.
- Author lists: commas only ("A, B, C"). Use "and" only for two-author papers ("A and B"). Underline (`\adv{}`) co-authors who were advisees when the paper was written.
- Venue names: "Proceedings of the VLDB Endowment (\textbf{PVLDB})", "Proceedings of the ACM on Management of Data (\textbf{PACMMOD})", and "DAMON" (not DaMoN).
- Award `note`s have no trailing period.
- Talk and paper titles use title case.
- Mentoring lists are newest first: by end date ("now" counts as latest), except Undergraduate Researchers, which are sorted by start date.
- After every change, run `make` and confirm it compiles cleanly.

## Macros (defined in athcv.sty)
| Macro | Use |
|---|---|
| `\cvsection{Title}` | Top-level section (bold small caps) |
| `\cvsubsection{Title}` | Bold sub-heading (e.g. `Postdocs`, a year in Talks) |
| `\cvsubsubsection{Title}` | Indented bold sub-sub-heading |
| `\cventry{text}` | Indented list line (mentoring, service, talks, …) |
| `\setlength\cventryskip{2pt}` | Optional, right after `\cvsection`: row spacing for that section |
| `\dated{2026}{text}` | Date-column row (honors, grants, student awards) |
| `\membership{2010-now}{text}` | Professional memberships row |
| `\job{05/2025 – now}{Role}{Organization}{City, ST, USA}` | Experience row |
| `\degree{Degree\textmd{, Month Year}}{Institution}{Thesis line \\ Advisor line}` | Education |
| `\phdgrad{Name (MM/YYYY-MM/YYYY)}{Dissertation title}{First position}` | Ph.D. graduates |
| `\teachinst{\textbf{University,} Department}` / `\course{Course}{Terms}` | Teaching |
| `\patent{Title}{Number. \href{url}{link}}` | Patents |
| `\pubcategory{Title}` + `\begin{papers} … \end{papers}` | Publication category |
| `\paper{authors=…, title=…, venue=…, year=…, url=…}` | One publication (see below) |
| `\me` | Bold "M. Athanassoulis" |
| `\adv{X. Name}` | Underlined advisee co-author |
| `\award{…}` / `\awardbf{…}` / `\awardrm{…}` | Red italic / bold / upright award note |

### `\paper` keys
`authors`, `title` (no quotes; they're added), `venue` (everything after the title up to the year, including `Vol.`/`pp.` and the bold venue abbreviation like `(\textbf{PVLDB})`), `year` (bolded), `after` (optional text after the year, e.g. `(\textit{to appear})` or `(abstract)`), `url` (renders as a blue "link"; leave empty for none), `note` (optional, e.g. award notes using `\award{}`). Missing year → omitted.

Example:
```latex
\paper{
  authors = {\adv{T. Papon}, \me},
  title   = {ACEing the Bufferpool Management Paradigm for Modern Storage Devices},
  venue   = {In Proceedings of the IEEE International Conference on Data Engineering (\textbf{ICDE}), pp. 1326-1339},
  year    = {2023},
  url     = {https://doi.org/10.1109/ICDE55515.2023.00106},
}
```

## Fonts
Garamond (Monotype, as shipped with MS Word) is loaded from `fonts/` if present, otherwise from Word's bundled fonts in `/Applications/Microsoft Word.app/Contents/Resources/DFonts/`. If neither exists (e.g. Overleaf), EB Garamond is used and a warning is printed. The header and footer use Tahoma (a macOS system font).
