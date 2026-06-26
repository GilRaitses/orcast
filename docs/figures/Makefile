# docs/figures/Makefile
# Run from this directory: make all / make fig-01-erd-dynamodb / make clean

TIKZ_FIGS := fig-01-erd-dynamodb fig-02-data-layer fig-03-workflow \
             fig-04-auth-flow fig-05-decisiondb-mapping \
             fig-06-provenance-graph fig-07-gate-pipeline fig-08-architecture

CONVERT := $(shell command -v pdftoppm 2>/dev/null || echo "gs")

.PHONY: all clean $(TIKZ_FIGS) fig-08-architecture

all: $(TIKZ_FIGS) fig-08-architecture

$(TIKZ_FIGS):
	@echo "Building $@..."
	cd $@ && \
	  TEXINPUTS=../shared/: latexmk -pdf -interaction=batchmode figure.tex 2>/dev/null || \
	  TEXINPUTS=../shared/: pdflatex -interaction=batchmode figure.tex
	@# Rasterise to PNG at 300 dpi
	@if command -v pdftoppm >/dev/null 2>&1; then \
	  pdftoppm -r 300 -png $@/figure.pdf $@/figure && mv $@/figure-1.png $@/figure.png 2>/dev/null || true; \
	elif command -v gs >/dev/null 2>&1; then \
	  gs -dNOPAUSE -dBATCH -sDEVICE=pngalpha -r300 -sOutputFile=$@/figure.png $@/figure.pdf; \
	fi
	@echo "  -> $@/figure.pdf  $@/figure.png"

post-build-fig-08:
	@cp docs/figures/fig-08-architecture/figure.png web/public/demo-slides/architecture.png 2>/dev/null || true
	@cp docs/figures/fig-08-architecture/figure.png docs/devpost/figures/architecture.png 2>/dev/null || true

clean:
	for f in $(TIKZ_FIGS); do \
	  cd $$f && latexmk -C figure 2>/dev/null; rm -f figure.aux figure.log figure.fls figure.fdb_latexmk; cd ..; \
	done

verifyall:
	@for f in $(TIKZ_FIGS); do \
	  if [ -f $$f/figure.pdf ]; then echo "OK $$f"; else echo "MISSING $$f/figure.pdf"; fi; \
	done
