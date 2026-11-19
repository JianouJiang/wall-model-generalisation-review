# Wall-model generalisation review

Research materials for **When can a wall-model test support a new prediction?** Authorship is to be decided.

**The current manuscript is a corrected critical review for expert feedback.** The earlier numerical claims about the prevalence of transfer, the seven outcome categories and the “9 of 18” quantity-only contrast have been withdrawn. The corrected paper makes no field-wide estimate of validation, success or failure. It distinguishes coupled validation, transfer beyond calibration, relative benefit and absolute accuracy, using source-checked examples.

- [Current corrected manuscript](manuscript/main.pdf)
- [Scientific corrections and audit scope](docs/scientific-corrections.md)
- [Agrawal source-version and scope reconciliation](docs/agrawal-scope-audit.md)
- [Current findings and remaining research limits](docs/research-status.md)
- [Claim-support register](data/revision/claim_support.json)
- [Eligibility audit of all 33 records outside the historical cohort](data/revision/eligibility_audit.json)
- [Reproduction instructions](docs/reproducibility.md)
- [Figure design and data](docs/figure-design.md)
- [Data dictionary](docs/data-dictionary.md)

The [source dispositions](data/revision/source_dispositions.json) locate comparison designs in all 115 retrieved works. The [paired readings](data/revision/paired_readings.json) reconnect 79 earlier questions to runs and observables. The [periodic-hill tables](data/revision/hill_table_population.json) identify the five studies eligible for a common crossing comparison, including the run in which the bubble disappears. The [printed table digits](data/revision/table_digits.json) and the [resolved directions](results/revision/direction_resolution.json) state which changes survive rounding and the choice of reference. The [agreement record](data/revision/agreement_v2.json) gives the facts-based second reading of 74 works, the settlement of every disagreement and the decision for each count; the [derived memberships](results/revision/derived_memberships.json) give the counts quoted in the paper. The [pairings record](data/revision/reader_agreement.json) reports the second reading of 34 pairings. The [paired numerical results](results/revision/paired_error_changes.json), resolved directions and [design memberships](results/revision/eligible_units.json) are regenerated with the figures.

The original [17:29 circulation PDF](manuscript/circulation_snapshot_2026-11-18.pdf), historical 82-treatment coding and intermediate sensitivity calculations remain as **superseded research records**. They are not the current paper and must not be used to restore the withdrawn conclusions. Reproducing a stored calculation does not validate its source interpretation or denominator.

## Reproduce

Use Python 3.10 with the packages in `requirements.txt` and install the [journal template](manuscript/class/README.md). From the repository root, render the figures, compile the paper and check the build in this order.

    python3 -I code/reproduce.py
    (cd manuscript && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex)
    python3 -I code/check_current.py

For the public natural-convection deposit, run `python3 code/verify_he_profiles.py NaturalConvection.zip`, or add `--closure sst` for the second pair. Omit the zip argument to fetch the checksum-verified dataset from STFC.

The last command checks the numerical inputs, source records, captions, compiled bibliography and PDF using the LaTeX build files and the Poppler tools `pdftotext`, `pdftohtml` and `pdfinfo`.

For historical diagnostics only, use code/reproduce.py --historical. These calculations do not supply the current paper's conclusions.

## Reuse

Source papers remain at their publishers or original repositories. Only research metadata, derived records, figure code and manuscript materials are included here. The collection is not an exhaustive or fully reconciled census of the current journal literature. See [RIGHTS.md](RIGHTS.md).
