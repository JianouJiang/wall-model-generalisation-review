# Reproduction and verification

Use Python 3.10 and requirements.txt in a virtual environment. The recorded rendering environment uses matplotlib 3.5.1 and numpy 1.21.5. Font libraries can change PDF bytes; numerical and layout checks are the primary reproducibility checks.

## Current edition

Run code/reproduce.py to render the four figures. Figure 1 is a labelled physical schematic. Figure 2 uses data/revision/agrawal_validation.json. Figure 3 uses the published numerical values in data/revision/dupuy_table5.json. Figure 4 recomputes descriptive agreement from data/checklist_cases.json.

Run code/check_current.py after building manuscript/main.pdf. It checks current citations against the support record, caption limits, numerical inputs, historical-withdrawal wording, PDF page budget and prohibited circulation text. Figure rendering separately checks font sizes and layout.

Build the manuscript with latexmk from manuscript/. The template dependency is described in manuscript/class/README.md. No supplementary PDF is part of the current circulation manuscript; the original circulation snapshot is an archive, not an appendix.

## Historical diagnostics

code/reproduce.py --historical also runs analyse_scope.py and analyse_revision.py. The former reproduces the original 82-treatment coding under two scope choices. The latter records the intermediate 84-treatment diagnosis and source corrections. Wider eligibility defects mean neither supplies a current population estimate.

Historical data and results retain their original values for traceability. Their successful reproduction is a software consistency check, not independent verification of every source coding. Do not quote the superseded outcome or quantity-only counts as current findings.

## Export boundary

The repository contains research data, derivations and figure code. It does not redistribute the source-paper library. Obtain papers from the listed original sources. No unpublished contact list or correspondence is needed to reproduce the paper's current numerical illustrations.
