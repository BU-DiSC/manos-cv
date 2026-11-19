NAME := ManosAthanassoulisCV-EN
LATEXMK := latexmk -xelatex -interaction=nonstopmode -halt-on-error -jobname=$(NAME)

# Build $(NAME).pdf and copy it to the parent folder on every `make`.
all: $(NAME).pdf
	cp $(NAME).pdf ../$(NAME).pdf

$(NAME).pdf: cv.tex athcv.sty $(wildcard sections/*.tex)
	$(LATEXMK) cv.tex
	latexmk -c -jobname=$(NAME) cv.tex >/dev/null

clean:
	latexmk -C -jobname=$(NAME) cv.tex

.PHONY: all clean
