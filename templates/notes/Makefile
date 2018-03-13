LATEX=pdflatex
LATEXOPT=-shell-escape --synctex=1
NONSTOP=--interaction=nonstopmode

LATEXMK=latexmk
LATEXMKOPT=-pdf
CONTINUOUS=-pvc

MAIN=\EXPR{ name }
SOURCES=$(MAIN).tex Makefile $(MAIN).bib $(wildcard sections/*.tex)
TIKZDIR=images-tikz
OUTDIR=.
#SVGS := $(shell find images/*.svg -type f)
#FIGURES := $(shell find figures/* images/* -type f)
FIGURES=

all: $(MAIN).pdf $(MAIN).synctex.gz


$(OUTDIR):
	mkdir -p $(OUTDIR)

$(TIKZDIR):
	mkdir -p $(OUTDIR)/$(TIKZDIR)

.refresh:
	touch .refresh

$(OUTDIR)/$(MAIN).pdf: $(MAIN).tex $(SOURCES) $(FIGURES) $(OUTDIR) $(TIKZDIR)
	$(LATEXMK) $(LATEXMKOPT) -output-directory=$(OUTDIR)  -pdflatex="$(LATEX) $(LATEXOPT) $(NONSTOP) %O %S" $(MAIN)

once: $(MAIN).tex $(SOURCES) $(FIGURES) $(OUTDIR) $(TIKZDIR)
	$(LATEX) $(LATEXOPT) -output-directory=$(OUTDIR) $(NONSTOP) $(MAIN)

force:
	$(LATEXMK) $(LATEXMKOPT) -output-directory=$(OUTDIR) -pdflatex="$(LATEX) $(LATEXOPT) $(NONSTOP) %O %S" $(MAIN)

clean:
	$(LATEXMK) -output-directory=$(OUTDIR) -c $(MAIN)
	rm -f $(OUTDIR)/*.{bbl,blg,aux,auxlock,end,fls,log,out,fdb_latexmk,run.xml,tdo,lox}

purge: clean
	$(LATEXMK) -output-directory=$(OUTDIR) -C $(MAIN)
	rm -rf $(TIKZDIR)

svgs: $(SVGS:.svg=.pdf) $(SVGS:.svg=.eps)

%.pdf: %.svg
	inkscape --without-gui --export-pdf=$@ --export-text-to-path $<

%.eps: %.svg
	inkscape --without-gui --export-eps=$@ --export-text-to-path $<

.PHONY: all once force clean purge svgs
