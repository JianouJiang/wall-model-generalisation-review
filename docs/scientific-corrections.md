# Scientific correction record — 18 November 2026

The scientific review found defects beyond the initial Agrawal case. The correction changes the paper's claims, not just their wording.

## Findings and resolutions

| Problem | Resolution in the current paper |
|---|---|
| Scope-filtered Agrawal rows were interpreted as absent coupled validation | Acknowledge speed-bump and transonic coupled LES explicitly; keep physical scope separate |
| Coded preprint differed from accepted/published comparison | Use the published Agrawal comparison; distinguish other identified preprints and accepted manuscripts from journal versions |
| Residual absolute error was interpreted as failure to improve | Separate relative benefit, absolute error, required tolerance and uncertainty |
| Dupuy was used as a quantity-only favourable/adverse reversal | Withdraw that interpretation; published Table 5 shows both integrated stress errors improve |
| Jones comparisons used different near-wall meshes | Do not describe them as changing only the observable |
| Building-block results mixed internal and total error experiments | Report the practical-closure change explicitly |
| Scope sensitivity omitted wholly uncertain and disputed studies | Preserve the intermediate calculations as diagnostics; do not use them as a repaired denominator |
| Eligibility rules treated estimators, coupled-system tests and thermal/hydrodynamic evidence inconsistently | Audit all 33 records outside the historical 82; withdraw population estimates |
| In-calibration validation was described as unable to expose failure | State that it can reveal error; distinguish it from transfer evidence |
| Constrained mean stress was treated as entirely uninformative | Retain it as a balance/implementation check while distinguishing constitutive validation |
| Retrospective checklist applications implied predictive validation | Report only label agreement; disclose universal abstention, shared sources, known outcomes and later revisions |
| A match on every numerical detail made the checklist unhelpfully absolute | Permit justified extensions supported by physical reasoning and sensitivity evidence at the user's tolerance |

## What was checked

The audit reviewed all 33 records outside the original 82-treatment set at the eligibility-passage level. The [eligibility record](../data/revision/eligibility_audit.json) states each decision and its basis. This is not a complete new coding of those papers. It exposed further boundaries requiring consistent definitions, including wall-stress estimators, mixed heat/hydrodynamic assessments and numerical-method studies.

Every empirical comparison retained in the current manuscript has an entry in the [support register](../data/revision/claim_support.json). Published sources were checked for Agrawal, Dupuy, Lozano-Durán/Bae, Bae/Koumoutsakos and Raje/Duraisamy. Detailed Hayat/Park, Mukha/Schlatter and Zhou/Bae examples cite the actual arXiv versions used. Jones/Utyuzhnikov is identified as an accepted manuscript. Background review identities and mathematical derivations have different evidential roles, recorded explicitly.

The thin-layer equation was checked from the stated differential balance, including signs, stress convention, constant density, pressure assumption and omitted body force. Channel/pipe constraints now require stationarity, appropriate symmetry/averaging and discrete conservation. The figure of a reversed layer is explicitly schematic.

Dupuy's published Table 5 was also visually checked. The N=4 ratios are 0.067/0.806 and 0.308/0.686. Both are below one. No reattachment-location improvement is inferred from those integrals.

## Withdrawn aggregate claims

The earlier “fewer than half”, seven outcome-category totals, “9 of 18”, causal-grade totals and later-outcome hit rates are not findings of this edition. They cannot be repaired by changing Agrawal alone. The 82/84-study computations remain reproducible historical diagnostics, with their restricted scope and unresolved eligibility stated in their status metadata.

Reinstating a prevalence analysis would require a new, consistently applied eligibility definition, version reconciliation and complete extraction for the resulting denominator, followed by a fresh audit. That is a separate research extension, not a prerequisite disguised as a completed result.

## Current scientific scope

The deliverable is a critical review with source-checked examples and a proposed checklist. It is suitable to request expert criticism of those arguments. It is not a certified universal model ranking, an exhaustive literature census, a validated predictive instrument or a journal acceptance guarantee. Historical process milestones do not establish those properties.
