# Reproduction and verification

Use Python 3.10 and requirements.txt in a virtual environment. The recorded rendering environment uses matplotlib 3.5.1 and numpy 1.21.5. Font libraries can change PDF bytes; numerical and layout checks are the primary reproducibility checks.

## Current edition

Run code/reproduce.py to render the four figures. Figure 1 is a labelled physical schematic. Figure 2 reads the paired studies, numerical values, categorical observations and source locators in data/revision/comparison_map.json. The manuscript check repeats the interpolation of the three approximate step reattachment positions from the recorded source-figure coordinates. Figure 3 normalises the two integrals in data/revision/dupuy_table5.json against their respective baselines and plots 24 local readings in data/revision/outer_input_error.json. The shading denotes the authors' prose summary for practical closures. Figure 4 compares the paired labels in data/revision/checklist_choices.json with the archived flags in data/checklist_cases.json. The separate Agrawal correction record remains in data/revision/agrawal_validation.json.

code/reproduce.py first runs code/derive_memberships.py, which derives the group memberships from the recorded facts, and code/check_agreement.py, which redraws the random sample from its seed and recomputes the agreement statistics, bootstrap bounds and decisions (numpy only). code/reproduce.py also runs code/resolve_directions.py, which uses only the standard library. It reads the printed digit strings in data/revision/table_digits.json, bounds each change in absolute error over the rounding intervals and reported reference intervals, and writes results/revision/direction_resolution.json.

Run code/check_current.py after building manuscript/main.pdf. It ties the periodic-hill, channel and bump sentences, every count of reports and tests in the text and Box 1, and the types of test in Table 2 to the recomputed values. It checks current citations against the support record, caption limits, numerical inputs, historical-withdrawal wording, PDF page budget and prohibited circulation text. It verifies the Figure 4 case identifiers and counts for all eight combinations. Poppler's pdftohtml checks the font, size, colour and relative position of every panel letter and heading in the figure PDFs.

Build the manuscript with latexmk from manuscript/. The template dependency is described in manuscript/class/README.md. No supplementary PDF is part of the current circulation manuscript; the original circulation snapshot is an archive, not an appendix.

To re-read the boundary-layer values directly, run `python3 code/verify_fig3_source.py /path/to/published.pdf` with PyMuPDF installed. The verifier finds the intersections of the published error traces with the four station coordinates and converts the logarithmic ordinates into percentages. The data file includes the digest of the PDF used. [Source article, Fig. 9](https://doi.org/10.1017/jfm.2023.331)

For the tripped boundary-layer comparison, run `python3 code/verify_profile_source.py /path/to/published.pdf` with PyMuPDF installed. The script re-reads the two simulations and the DNS profile at the marked wall distance in Figure 25. The source record includes the PDF fingerprint, axes, rounding and plotting resolution. [Chen and He, Fig. 25](https://doi.org/10.1017/jfm.2022.1024)

## Historical diagnostics

code/reproduce.py --historical also runs analyse_scope.py and analyse_revision.py. The former reproduces the original 82-treatment coding under two scope choices. The latter records the intermediate 84-treatment diagnosis and source corrections. Wider eligibility defects mean neither supplies a current population estimate.

Historical data and results retain their original values for traceability. Their successful reproduction is a software consistency check, not independent verification of every source coding. Do not quote the superseded outcome or quantity-only counts as current findings.

## Export boundary

The repository contains research data, derivations and figure code. It does not redistribute the source-paper library. Obtain papers from the listed original sources. No unpublished contact list or correspondence is needed to reproduce the paper's current numerical illustrations.
