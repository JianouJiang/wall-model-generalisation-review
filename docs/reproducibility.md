# Reproducibility boundaries

The public package can recompute claim categories, favourable/adverse flags and exposure bounds for the existing 82-claim cohort under two scope rules. It can redraw all four baseline figures and rebuild the public manuscript from its exported number macros, tables and bibliography.

The public package does not reconstruct the initial screening, source coding, attribution grading, pair adjudication or retrospective checklist assessment from primary publications. Those result snapshots are provided for inspection. The fixed-cohort sensitivity is not the complete originally specified sensitivity across all screened studies; see the scope audit.

## Environment

The archived figure environment is Python 3.10, NumPy 1.21.5 and Matplotlib 3.5.1, with DejaVu Sans. Install the pinned requirements in a virtual environment. Other Matplotlib versions can change geometry and the behaviour of the layout checks, even if the counts are identical. `-I` prevents unrelated user-site packages from changing the environment.

## Checks

`code/analyse_scope.py` evaluates the stored alternatives and compares all 82 claim results in both variants with the reference snapshot, including exposure states. It also checks baseline categories and favourable/adverse flags against `data/claims.csv`.

The figure scripts assert the category sums and contrast counts they plot. They enforce a minimum base text size of 8 pt at 160 mm printed width, check layout intersections and clipping, and write a text inventory and layout report in `results/figures/`. Mathematical subscripts follow the caption's smaller script size.

During preparation, all four reproduced figure PDFs were byte-identical to the archived originals. Their plotted values were also compared with the original result files. This verifies the public port, not the scientific interpretation of the underlying papers.

A second run in a fresh virtual environment with the pinned wheels reproduced the analysis, all plotted values and all figure text inventories, and passed every layout check. Its PDF bytes differ from those of the system environment: the FreeType versions are 2.6.1 and 2.11.1 respectively, with identical DejaVu Sans font-file hashes. The verification record distinguishes semantic reproduction from byte identity. All 60 reference labels match the rebuilt 15-page public manuscript.

`SHA256SUMS` records the released files. Verify it from the repository root with `sha256sum -c SHA256SUMS`. Generated files can vary across environments, especially the compiled manuscript's PDF metadata. The historical circulation PDF is preserved unchanged.
