# Wall-model generalisation review

Research materials for **Why wall models fail to generalise, and how to judge the evidence before use**. Authorship is to be decided.

**The current manuscript is a corrected critical review for expert feedback.** The earlier numerical claims about the prevalence of transfer, the seven outcome categories and the “9 of 18” quantity-only contrast have been withdrawn. The corrected paper makes no field-wide estimate of validation, success or failure. It distinguishes coupled validation, transfer beyond calibration, relative benefit and absolute accuracy, using source-checked examples.

- [Current corrected manuscript](manuscript/main.pdf)
- [Scientific corrections and audit scope](docs/scientific-corrections.md)
- [Agrawal source-version and scope reconciliation](docs/agrawal-scope-audit.md)
- [Current findings and remaining research limits](docs/research-status.md)
- [Claim-support register](data/revision/claim_support.json)
- [Eligibility audit of all 33 records outside the historical cohort](data/revision/eligibility_audit.json)
- [Reproduction instructions](docs/reproducibility.md)
- [Data dictionary](docs/data-dictionary.md)

The original [17:29 circulation PDF](manuscript/circulation_snapshot_2026-11-18.pdf), historical 82-treatment coding and intermediate sensitivity calculations remain as **superseded research records**. They are not the current paper and must not be used to restore the withdrawn conclusions. Reproducing a stored calculation does not validate its source interpretation or denominator.

## Reproduce

Use Python 3.10 and install requirements.txt in a virtual environment. Run:

    python3 -I code/reproduce.py
    python3 -I code/check_current.py

The first command renders the current four figures. The second checks the manuscript, source-support coverage, numerical inputs, captions and compiled PDF. LaTeX, pdftotext and pdfinfo are required for PDF checks. Build with latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex from manuscript/, using the template described in manuscript/class/README.md.

For historical diagnostics only, use code/reproduce.py --historical. These calculations do not supply the current paper's conclusions.

## Reuse

Source papers remain at their publishers or original repositories. Only research metadata, derived records, figure code and manuscript materials are included here. The collection is not an exhaustive or fully reconciled census of the current journal literature. See [RIGHTS.md](RIGHTS.md).
