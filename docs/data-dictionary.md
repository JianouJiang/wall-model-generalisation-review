# Data dictionary

## Current corrected edition

Read data/revision/STATUS.json first. The current paper uses comparison_map.json for the selected multi-study comparisons, dupuy_table5.json for published numerical values, claim_support.json for retained claims, eligibility_audit.json for the 33 eligibility checks, and historical_source_manifest.json for exact archived copy identities. The separate source/scope correction is retained in agrawal_validation.json. Only the agreement labels in checklist_cases.json enter the current retrospective illustration.

In comparison_map.json, each row specifies the selected comparison, exact source location, support-register identifiers, changed choices and examined quantities. This is a selective illustration of the review's cases. An unmarked feature is not encoded for that example; it is not a negative finding about the paper. The columns are not mutually exclusive interventions and their totals have no population interpretation.

Figure 3's second part uses outer_input_error.json. The relations "less than" and "approximately" must be preserved, as must the distinction between the reported 5–15% range and an uncertainty interval. No pointwise source values are digitised. Figure 4's case numbers map in order to the case identifiers in results/figures/fig4_values.json; no later-outcome classifications enter its counts.

The other files described below are historical research records. The original outcome flags conflated some relative and absolute comparisons, and the historical cohort has unresolved eligibility inconsistencies. Their counts are withdrawn from the current manuscript. data/revision/test_codings.json and results/revision/design_audit.json record an intermediate 84-study diagnosis, not a repaired census. source_versions.json describes that earlier diagnostic; historical_source_manifest.json covers all 115 archived sources.

## Historical export

These files are a research export of the 18 November 2026 circulation baseline. They preserve scientific values and uncertainty alternatives, with public file names and source locations. No full-text articles are embedded.

| File | Contents |
|---|---|
| `data/studies.csv` | 115 indexed studies: bibliographic identifiers, source/version, treatment class, and main-count membership. It is broader than the 82-claim analysis. A search-record year can differ from the final issue year; use the DOI to resolve a publication. |
| `data/search_records.csv`, `data/search_log.csv`, `data/search_protocol.json` | Bibliographic metadata for the 2,543 title/abstract screening inputs, 29 corpus-search retrieval records, query strings and screening criteria. Abstracts and raw API responses are not included. The full-text scope amendment is stated separately from the initial screening wording. |
| `data/claims.csv` | 82 baseline claims, split into 57 `new` and 25 `pilot`; categories, outcome flags, attribution codes and bibliographic links. The pilot informed the coding scheme. |
| `data/test_codings.json` | 460 test rows attached to those claims, with semantic fields, unresolved alternatives and source locations. A row is a coded comparison, not necessarily a distinct physical simulation. |
| `data/expected_claim_results.json` | Reference claim results for the baseline and unknown-included sensitivity, checked by the public analysis. |
| `data/claim_categories.json` | Counts by cohort and treatment class for baseline Figure 2. |
| `data/contrasts.json`, `data/contrast_pairs.json` | Claim-level and pair-level contrast summaries for baseline Figure 3. |
| `data/quantity_pairs.json` | Quantity names and cited sections for the baseline quantity contrasts. |
| `data/later_tests.json` | Baseline cross-tabulations of later tests, used in Figure 4a. |
| `data/checklist_cases.json` | Results for 13 checklist cases, used in Figure 4b. `A` and `B` label coding passes; they do not identify people. `H` and `P` distinguish cases not used and used to formulate step 5. |
| `data/reference_labels.json` | Names, years and reference numbers as printed in the baseline manuscript. |
| `manuscript/numbers.tex` | Snapshot of manuscript number macros. Apart from the scope calculation, their upstream derivations are outside this export. |

## Test fields

`scope` is `yes`, `unknown`, or an exclusion such as `no: compressible`. `mode` distinguishes a priori reference inputs from a coupled solver. `calibration_family` is `inside`, `outside` or `unknown`. `observable_status` is `free`, `fixed` or `unknown`. `cause_exercised` is `yes`, `no` or `unknown`. `flow`, `quantity`, `setup`, `baseline` and `source_locations` describe the test and where it is reported.

`result_flag` records one of the favourable states (improvement shown, preserved accuracy, agreement with reference without a matched comparison), adverse states (regression, improvement not shown, disagreement with reference without a matched comparison), or no resolved flag. These labels concern the coded comparison, not the overall scientific quality of a paper.

`outcome_basis` distinguishes a source statement, numerical evidence without a stated reference uncertainty, and an outcome resolved against such uncertainty. “Words only” describes the evidence used to code that comparison; it must not be paraphrased as “the paper contains no numbers”.

`alternatives` records unresolved candidate values. A literal `unknown` means the field is unknown under the coding; `undecided` with alternatives means competing coded interpretations are carried through the calculation. Their meaning must not be conflated with proven absence in the source. Missing fields are unassessed, not false.

## Exposure and category definitions

A test meets the review's exposing-test rule when it is coupled, outside the coded calibration family, on a free quantity, and exercises the targeted cause. The definition concerns evidence for transfer; an a priori test or a test within calibration can still reveal model error. A favourable flag requires an exposing test. An adverse flag is counted from any included coupled test, whether or not it meets that transfer criterion.

| Category | Rule |
|---|---|
| 1a | Favourable exposing test including improvement, with no adverse coupled flag |
| 1b | Favourable exposing test without an improvement flag, with no adverse coupled flag |
| 2 | Favourable exposing test and an adverse coupled flag |
| 3 | Adverse coupled flag without a favourable exposing test |
| 4 | Exposing test but neither favourable nor adverse flag |
| 5 | No confirmed exposing test or adverse flag; at least one test has unknown exposure |
| 6 | No included test meets or may meet the exposing-test rule |
| 7 | No tests in the category function; claims with no in-scope rows are separately identified as out of scope |

All relevant combinations of the stored alternatives are evaluated. A result is **confirmed** when it holds under every combination and **possible** when it holds under at least one. These are not sampling-error confidence intervals. Category 3 is not a synonym for absence of exposing tests: exposure must be counted separately from the result category.

The attribution labels in `claims.csv` are C1 (states the model can return), C2 (retained balance), C3 (input information), C4 (solver coupling), and O (effects outside these four model components). Their grades are supplied as snapshots, not recomputed by the scope script.
