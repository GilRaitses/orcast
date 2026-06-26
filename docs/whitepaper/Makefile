# Wave Set W whitepaper build
# Run from docs/whitepaper/

PAPER = LX/Raitses_orcast_2026.tex
BUILD = Build
FIGURES_DIR = LX/Figures

.PHONY: pdf figures audit clean

pdf: figures
	latexmk -pdf -bibtex -outdir=$(BUILD) $(PAPER)

figures:
	@echo "Compiling mermaid figures..."
	@for f in $(FIGURES_DIR)/*.mmd; do \
		out="$${f%.mmd}.pdf"; \
		mmdc -i "$$f" -o "$$out" -t dark && echo "  ✓ $$out"; \
	done

audit:
	python3 ../../tools/testing/reference_audit.py \
		--research-dir research/ \
		--bib-out LX/references.bib \
		--audit-out LX/reference_audit.txt

clean:
	rm -rf $(BUILD)/*.aux $(BUILD)/*.bbl $(BUILD)/*.bcf $(BUILD)/*.blg \
	       $(BUILD)/*.fdb_latexmk $(BUILD)/*.fls $(BUILD)/*.log \
	       $(BUILD)/*.out $(BUILD)/*.run.xml $(BUILD)/*.toc \
	       $(BUILD)/*.synctex.gz

cleanall: clean
	rm -f $(BUILD)/*.pdf
