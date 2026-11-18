# Agrawal et al. (2024): correction and unresolved scope questions

Audit date: 18 November 2026 (UK).

**Agrawal et al. did perform coupled LES validations. A statement implying that this paper has zero coupled tests is wrong.** The zero in the baseline is the number remaining after the review's scope filter, not the number in the paper. This distinction also applies to other studies whose test rows were excluded or classified as scope-unknown.

Source: *Nonequilibrium wall model for large eddy simulations of complex flows exhibiting turbulent smooth body separation*, Physical Review Fluids 9, 124603, [DOI: 10.1103/PhysRevFluids.9.124603](https://doi.org/10.1103/PhysRevFluids.9.124603). The copy coded for this review is [arXiv:2407.11390v1](https://arxiv.org/abs/2407.11390v1), dated 16 July 2024.

**Additional source-version finding.** The [APS accepted manuscript](https://link.aps.org/accepted/10.1103/PhysRevFluids.9.124603), dated 14 November 2024, differs materially from that preprint. Section V.A, Figure 7 adds equilibrium-model velocity comparisons and describes better agreement of the proposed model on coarse and medium grids. Figure 8 adds Reynolds-shear-stress comparisons. The preprint-based velocity code “disagreement with reference (no matched comparison)” therefore needs reassessment. This sensitivity keeps the old codes fixed; it is not a corrected assessment of the accepted paper. Recode the appropriate source version before deciding the revised category or any quantity-only contrast.

## What was filtered

Study `N418` has **nine coded test rows: eight coupled rows and one a priori row**. Rows represent coded comparisons or quantities, not eight distinct LES simulations. The baseline keeps only the a priori row. It excludes five coupled rows as scope-unknown and three coupled transonic rows as outside scope.

| Public test ID | Evidence in the coded source | Baseline scope |
|---|---|---|
| N418-T01 | NASA/Boeing speed bump: surface pressure, Sec. V.A Fig. 4a and Sec. V.C Fig. 8a | unknown |
| N418-T02 | Speed bump: skin friction, Sec. V.A Fig. 4b | unknown |
| N418-T03 | Speed bump: mean velocity, Sec. V.A Fig. 5 | unknown |
| N418-T04 | Transonic Bachalo–Johnson bump: pressure, Sec. VI.B Fig. 10 | excluded: compressible |
| N418-T05 | Transonic bump: velocity, Sec. VI.B Fig. 11 | excluded: compressible |
| N418-T06 | A priori reference-input tests, Sec. IV Fig. 2 | included |
| N418-T07 | Speed bump: momentum thickness and shape factor, Sec. V.A Fig. 6 | unknown |
| N418-T08 | Transonic bump: separation/reattachment, Sec. VI.C Fig. 12 | excluded: compressible |
| N418-T09 | Additional coded pressure comparison for the speed bump, Sec. V.A | unknown |

T01 and T09 require comparison-unit reconciliation; their presence must not be presented as two independent simulations. The export preserves the original row identities rather than silently merging them.

The review covers smooth-wall, incompressible or low-Mach flows. Its amended rule excludes a row when an excluded condition is stated, marks it unknown when the text raises but does not settle that condition, and otherwise includes it. The five speed-bump rows were marked unknown from Sec. II.B's description of charLES as a compressible Navier–Stokes solver. **Solver formulation alone does not establish the flow's Mach regime.** The zero-Mach-limit statement there describes the discretisation's conservation property, not a numerical Mach value for the speed-bump case. A case-specific regime statement, in the published article or a linked setup description, is needed to settle the classification consistently.

The explicitly transonic cases at Mach 0.85, 0.875 and 0.90 remain outside the stated incompressible/low-Mach review scope. They nevertheless establish that the paper contains coupled validation; they must not disappear from an account of what the authors tested.

## Recomputed sensitivity within the existing cohort

`python3 -I code/analyse_scope.py` repeats the category and exposure calculation with unknown-scope rows included. It keeps all other coded values and alternatives fixed. The inputs are `data/test_codings.json`; the results are `results/scope_sensitivity.json` and `results/claim_results.json`.

There are 31 literal unknown-scope rows, all coupled, across 11 retained claims. A twelfth claim, N291, has unknown among its scope alternatives. Three categories change:

| Study | Baseline | Unknown included |
|---|---|---|
| N291, Park et al. (2013), DOI 10.2478/ijnaoe-2013-0116 | undetermined | 1a: favourable exposing test, no adverse coupled result |
| N418, Agrawal et al. (2024) | 6: no included test meets the exposing-test rule | 2: favourable exposing test and an adverse coupled result |
| P04, Yao et al., DOI 10.1299/jfst.2021jfst0007 | 6 | 1a |

The claim-census categories are:

| Category | Baseline | Unknown included |
|---|---:|---:|
| 1a | 1 | 3 |
| 1b | 0 | 0 |
| 2 | 18 | 19 |
| 3 | 35 | 35 |
| 4 | 0 | 0 |
| 5 | 6 | 6 |
| 6 | 15 | 13 |
| 7 | 0 | 0 |
| undetermined | 7 | 6 |
| total | 82 | 82 |

The category-1 bound is 2–4 in the baseline and 4–5 in the sensitivity. It is not just the sum of certain 1a and 1b assignments: a claim uncertain between 1a and 1b is certainly in their union.

The design-based exposure bound rises from **32–36 to 35–38 of 82**. For the 57 non-pilot claims it rises from **19–23 to 21–24**. “Fewer than half” holds for both of these cohorts under this perturbation; it does not hold for the pilot subset alone. “Exposing” is a defined transfer criterion, not a statement that other tests are incapable of detecting error.

## What this run does not settle

**Entirely scope-excluded studies.** P16 ([10.1017/jfm.2025.10171](https://doi.org/10.1017/jfm.2025.10171)) and N444 ([10.1038/s41598-020-69671-y](https://doi.org/10.1038/s41598-020-69671-y)) were excluded entirely for unknown scope. They have no adjudicated claim record in the exported 82-claim cohort. A full implementation of the originally specified unknown-scope sensitivity must reconsider them and document any denominator changes. The present calculation is a fixed-cohort sensitivity, not that complete analysis.

**The “9 of 18” quantity-only finding.** Including unknown scope produces 19 confirmed mixed claims, but a new numerator has not been established. The affected mixed claims are N357, N358, N418, N626 and P19. Each needs its favourable/adverse pairs checked under the revised scope. It is insufficient to inspect only N418 or assume the new answer is “9 or 10 of 19”.

For N418 specifically, Sec. V.A Fig. 4 reports better pressure/skin-friction predictions relative to an equilibrium model; Fig. 5 reports velocity discrepancies against quasi-DNS on coarse and medium grids. These statements do not by themselves establish that the paired outcomes differ **only** in quantity. The grid, station, parameter, reference and meaning of “favourable” must be aligned. Improvement relative to a baseline and absolute agreement with reference data answer different questions.

**Source and coding quality.** Numerical reproduction verifies the derivation from stored codes. It does not prove that the codes correctly represent the publications. Unknown information, disagreement between coding interpretations, and a physically excluded case must remain distinct. Uncertainty bounds are alternative-coding bounds, not confidence intervals.

## Corrected description

> Agrawal et al. (2024) validates its model in coupled LES of the NASA/Boeing speed bump and the transonic Bachalo–Johnson bump. The review's baseline scope filter retains only its a priori comparison, so its baseline category is not a description of the paper's full validation record. Including its unknown-scope speed-bump rows changes its category to mixed favourable/adverse evidence. The scope decision and the comparison pairs require reassessment before circulation as a settled finding.
