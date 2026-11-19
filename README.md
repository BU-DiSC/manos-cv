# manos-cv

Curriculum Vitae of Manos Athanassoulis, written in LaTeX.

- **Web version:** https://bu-disc.github.io/manos-cv/
- **PDF:** https://bu-disc.github.io/manos-cv/ManosAthanassoulisCV-EN.pdf

## Layout
- `cv.tex`: title block and section order
- `sections/*.tex`: content, one file per section (semantic macros only)
- `athcv.sty`: all styling for the PDF
- `tools/build_html.py` + `tools/cv.css`: render the same sources as a web page

## Build
```bash
git config core.hooksPath .githooks   # once per clone: pre-commit rebuilds the PDF
make                                   # → ManosAthanassoulisCV-EN.pdf (also copied to ../)
python3 tools/build_html.py            # → site/index.html (local preview)
```

The PDF uses MS Garamond, which ships with Microsoft Office and is not redistributable. It is read from a local `fonts/` folder (git-ignored) or from Word's bundled fonts. That's why the PDF is built locally and committed. On every push to `main`, GitHub Actions renders the HTML and publishes it to GitHub Pages together with the committed PDF.
