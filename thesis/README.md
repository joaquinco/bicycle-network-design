# Building the documents

Old document:
```
cd doc
pdflatex document.tex
biber document.bcf
pdflatex document.tex
```

After having changed the document.tex just run pdflatex

Latest document:
```
cd doc-udelar
pdflatex tesis.tex
bibtext tesis
pdflatex tesis.tex
```
