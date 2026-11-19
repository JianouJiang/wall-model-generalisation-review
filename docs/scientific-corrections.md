# Scientific correction record — 18 November 2026

The scientific review found defects beyond the initial Agrawal case. The correction changes the paper's claims, not just their wording.

## Findings and resolutions

| Problem | Resolution in the current paper |
|---|---|
| Scope-filtered Agrawal rows were interpreted as absent coupled validation | Acknowledge speed-bump and transonic coupled LES explicitly; keep physical scope separate |
| Coded preprint differed from accepted/published comparison | Use the published Agrawal comparison; distinguish other identified preprints and accepted manuscripts from journal versions |
| Residual absolute error was interpreted as failure to improve | Separate relative benefit, absolute error, required tolerance and uncertainty |
| Dupuy was used as a quantity-only favourable/adverse reversal | Withdraw that interpretation; published Table 5 shows both integrated stress errors improve |
| Jones and Utyuzhnikov compared complete diffuser calculations on different transverse meshes | The interface calculation recovered recirculation and improved total pressure drop. Their separate Robin/Dirichlet experiment tests how the boundary condition on turbulent kinetic energy affects the separation bubble. |
| Building-block results mixed internal and total error experiments | Report the practical-closure change explicitly |
| Scope sensitivity omitted wholly uncertain and disputed studies | Preserve the intermediate calculations as diagnostics; do not use them as a repaired denominator |
| Eligibility rules treated estimators, coupled-system tests and thermal/hydrodynamic evidence inconsistently | Audit all 33 records outside the historical 82; withdraw population estimates |
| In-calibration validation was described as unable to expose failure | State that it can reveal error; distinguish it from transfer evidence |
| Constrained mean stress was treated as entirely uninformative | Retain it as a balance/implementation check while distinguishing constitutive validation |
| Retrospective checklist applications implied predictive validation | Report only label agreement; disclose universal abstention, shared sources, known outcomes and later revisions |
| A match on every numerical detail made the checklist unhelpfully absolute | Permit justified extensions supported by physical reasoning and sensitivity evidence at the user's tolerance |

## What was checked

The audit reviewed all 33 records outside the original 82-treatment set at the eligibility-passage level. The [eligibility record](../data/revision/eligibility_audit.json) states each decision and its basis. This is not a complete new coding of those papers. It exposed further boundaries requiring consistent definitions, including wall-stress estimators, mixed heat/hydrodynamic assessments and numerical-method studies.

Every empirical comparison in the manuscript points to its edition and source location. Hayat and Park’s numerical friction signs use the arXiv v1 traces. Published Mukha, Parsani and Schlatter Table VII gives the paired coupled/offline stress errors. Table III gives a different coupled column for the same meshes, and the order of absolute errors on each mesh survives either reading. Zhou and Bae’s fixed-traction bump panel uses the JCP version of record. The separate learned-wall AIAA comparisons use arXiv v3. [Claim register](../data/revision/claim_support.json) · [Figure readings](../data/revision/displayed_comparisons.json)

The thin-layer equation was checked from the stated differential balance, including signs, stress convention, constant density, pressure assumption and omitted body force. Channel/pipe constraints now require stationarity, appropriate symmetry/averaging and discrete conservation. The figure of a reversed layer is explicitly schematic.

## Reconciliation of the abstract, figures and text

Dupuy et al. report two distinct measurements for the backward-facing step. Their Table 5 gives squared stress errors integrated along the wall. At four message-passing steps the model-to-baseline ratios are 0.067/0.806 for stress magnitude and 0.308/0.686 for the streamwise component. Both are below one. Their Fig. 16 gives the local streamwise shear. Its downstream zero crossing lies at approximately 4.7 step heights for the log law, 5.2 for the four-step graph model and 6.0 for the wall-resolved reference. The abstract and Fig. 2d use the crossings. Fig. 3a uses the integrals. The half-step tolerance in Section 4 is a worked example chosen for this review. The published figure gives no uncertainty interval for the crossings.

For the boundary-layer comparison in Fig. 3b, Lozano-Durán and Bae describe total errors of 5–15% with practical outer closures. Their Fig. 9 also shows a local equilibrium-model error of about 19% with the dynamic Smagorinsky closure at a streamwise Reynolds number of one million. The text and caption distinguish the authors' summary from the local reading. The swept-bubble example uses Renard and Deck's decomposition of the mean streamwise kinetic-energy budget. Equation (1) in this review integrates the thin-layer momentum equation.

The reviewed 11-page edition cites 28 works. The subsequent source reassessment also reconstructed a same-mesh periodic-hill comparison from five primary works and recovered the natural-convection profiles omitted from the article plots. [Hill-table inputs](../data/revision/hill_table_population.json) · [Natural-convection data](https://doi.org/10.5286/edata/979)

The abstract identifies the proposed procedure and its five-step checklist. The 13 retrospective cases used an earlier version. The two sets of proposed tests agreed on cause in eight cases, quantity class in ten and factor to vary in seven. All three choices agreed in three cases. Four of the cases helped formulate the earlier checklist's final step. Evaluating whether the procedure improves decisions in new applications requires a prospective comparison.

## Withdrawn aggregate claims

The earlier “fewer than half”, seven outcome-category totals, “9 of 18”, causal-grade totals and later-outcome hit rates are not findings of this edition. They cannot be repaired by changing Agrawal alone. The 82/84-study computations remain reproducible historical diagnostics, with their restricted scope and unresolved eligibility stated in their status metadata.

A new estimate requires a consistently applied eligibility rule, reconciliation of source editions, extraction for the whole resulting denominator and an independent audit. Its interpretation also depends on how the papers were selected and which full texts could be retrieved. The original collection can support conclusions about a defined sample if these conditions are met.

## Current scientific scope

The deliverable is a critical review with source-checked examples and a proposed checklist. It is suitable to request expert criticism of those arguments. It is not a certified universal model ranking, an exhaustive literature census, a validated predictive instrument or a journal acceptance guarantee. Historical process milestones do not establish those properties.
