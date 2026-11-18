# Wall-model generalisation review

Research materials for **Why wall models fail to generalise, and how to judge the evidence before use**. Authorship is to be decided.

**Provisional research draft: scientific validation is incomplete.** Agrawal et al. (2024) contains coupled LES validations. The original scope-filtered coding must not be described as evidence that the paper has no coupled tests. A source-version check also found material differences between its coded preprint and accepted manuscript. Read [the scope audit](docs/agrawal-scope-audit.md) before quoting the headline counts or using the draft for correspondence. The quantity-only contrast and the treatment of entirely scope-excluded studies remain open.

The package contains 115 study metadata records, 82 coded claims, 460 coded test rows, baseline result tables, four reproducible figures, manuscript sources and PDFs, and a runnable scope-sensitivity analysis. It contains the research export; its reproducibility boundaries are described below.

- [Public draft with the scope caveat](manuscript/main.pdf)
- [Original 18 November 2026, 17:29 UK circulation snapshot](manuscript/circulation_snapshot_2026-11-18.pdf), preserved as a historical baseline
- [Agrawal correction and scope sensitivity](docs/agrawal-scope-audit.md)
- [Data dictionary and coding definitions](docs/data-dictionary.md)
- [Research work still needed](docs/research-status.md)
- [Reproduction and verification record](docs/reproducibility.md)

The public draft retains the baseline figures and numerical findings, adds a visible provisional-status note, and describes the actual contents of this public package in its availability statements. It is not a scientifically corrected final manuscript.

## Reproduce

Use Python **3.10**; the rendering versions below match the archived figures.

```bash
python3.10 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -I code/reproduce.py
```

The analysis checks all 82 claims under both scope rules against the supplied reference results. The figure scripts check their drawn counts, text sizes and layout. Outputs go to `results/` and `figures/`.

To build the public manuscript, install LaTeX with `latexmk`, obtain the Springer Nature template as described in [manuscript/class/README.md](manuscript/class/README.md), and run:

```bash
cd manuscript
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

## What the sensitivity establishes

| Existing 82-claim cohort | Baseline | Unknown-scope rows included |
|---|---:|---:|
| Claims with an exposing test, confirmed–possible | 32–36 | 35–38 |
| Mixed favourable/adverse claims, confirmed | 18 | 19 |
| Favourable without adverse coupled evidence, confirmed–possible | 2–4 | 4–5 |
| Claims with undetermined category | 7 | 6 |

“Fewer than half” remains true for this fixed cohort, and separately for its 57 non-pilot claims. This run is a sensitivity to the coding choices, not a completed adjudication of them. It excludes two studies that were entirely omitted for unknown scope. The sensitivity numerator for “9 of 18” has **not** been established; five mixed-result claims need their pairs reassessed.

## Reuse and attribution

Study metadata and source locations identify the underlying publications; publisher full texts are obtained from their original sources. Scholarly author names in the bibliography are citations, not the authorship of this draft. See [RIGHTS.md](RIGHTS.md) for the rights statement and third-party template notices.
