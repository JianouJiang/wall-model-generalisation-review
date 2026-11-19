# Search, selection and data-extraction protocol

This document accompanies Box 1 and the Methods of the Review. `code/write_protocol.py` formats every number below from
the data file named beside it. Stage names follow the PRISMA 2020 flow diagram (Page et al., BMJ 372, n71, 2021). The
search is reported item by item as PRISMA-S asks (Rethlefsen et al., Syst. Rev. 10, 39, 2021). The synthesis counts
directions and pools no effect sizes (Campbell et al., BMJ 368, l6890, 2020). The protocol was not registered.

## 1. Search

- Database and platform: OpenAlex, works endpoint (`https://api.openalex.org/works`), field
  `title_and_abstract.search`. One index was searched. No trial registry, website, citation search, contact with authors
  or other method contributed records to the collection.
- Full search strategies, exactly as run, are in `data/search_protocol.json`. Each request, its date and the number of
  records returned are in `data/search_log.csv` (fetched on 17 November 2026).
  - Q1: RANS wall functions and near-wall treatments
  - Q2: wall-stress models and wall boundary conditions for large-eddy simulation
  - Q3: inner-outer models of the near-wall state or wall stress
  - Q4: learned wall models and learned wall-stress estimators
- Limits: publication dates 2000-01-01 to 2026-11-16. Filters applied to the
  retrieved records:
  - OpenAlex type is 'article'
  - primary location source type is 'journal' (records with no source are kept for the title and abstract screen and flagged)
  - publication year 2000-2026
  - language 'en' or missing
- No published search filter was used. No earlier strategy was reused, the search was not updated, and the strategy was
  not peer reviewed.
- Records identified: 5,323 from 4 searches.
- Deduplication: Across strands: identical OpenAlex id, then identical DOI, then identical normalised title (lower case, letters and digits only) with the same publication year. The kept record lists every strand that retrieved it. 386 duplicates were removed.
- Removed before screening: 2,238 not journal articles,
  100 with a primary source that is not a journal and 56
  not in English (2,394 in all). Source: `data/revision/search_flow.json`.

## 2. Screening on title and abstract

- 2,543 records were screened against criteria T1 to T3 of `data/search_protocol.json`
  (819 had no abstract in the index). Each record was screened as include,
  exclude or unclear. 1,808 were excluded.
- 735 reports were sought: 299 screened as include, 388 as unclear and
  48 on which two screenings disagreed. Source: `data/search_records.csv`.

## 3. Retrieval

- 171 of the 735 reports had a candidate open-access route and
  564 had none. 28 routes refused access and 23 returned an
  unusable file. 120 full texts were obtained. No paywall was circumvented. Source:
  `data/revision/retrieval_frame.csv`.
- Language check on the full text. A retrieved text fails if more than 20 % of its letters are kana, CJK ideographs or Hangul, or if fewer than 15 % of its Latin-script words are common English function words. 8 texts were flagged. 5 were
  set aside without assessment. 3 (P27, P32, P35) had been entered
  before the check was applied to every text and were assessed from their equations, figures, tables and English abstracts.

## 4. Eligibility

- 115 reports were assessed in full text. An eligible report names a wall treatment or wall-stress
  estimator and contains an identifiable test that compares a quantity with a reference. Editions of one work count once.
  108 reports are eligible, 2 are contested and 5 are excluded.
  Source: `data/revision/source_dispositions.json`.
- Primary scope: turbulent flow of a single-phase Newtonian fluid with constant properties and no buoyancy over smooth
  walls at Mach numbers up to 0.3. Of the 615 recorded tests, 60 lie
  outside it and 159 state neither a Mach number nor compressibility and
  count as inside it. 4 eligible reports test only flows outside the primary scope
  (N054, N189, N707, P02), which leaves 104 within it. Source:
  `data/revision/regime_facts.json`.
- Borderline reports (12). 5 use near-wall methods on grids that reach the
  viscous sublayer (N318, N372, N419, N445, N446).
  4 test stress estimators never presented as wall models
  (N011, N080, N719, P08).
  3 had eligibility disputed between the two extractions
  (N147, N166, N635).
- Counts are given on three bases: the collection; excluding borderline reports and comparisons on grids that reach the
  sublayer (N300-K04, N318-K01, N318-K02, N318-K04, N419-K02, N446-K01); and within the primary scope. The eligible reports number
  108, 96 and 104 on the three bases.

## 5. Data extraction: the three groups of evidence

- Rules fixed before extraction name the facts that define each group (`data/revision/wall_change_contrasts.json` stores the
  rule text). `code/derive_memberships.py` derives each group from the extracted facts. No group label is typed by hand.
- Controlled comparison of wall treatments: two coupled calculations that differ only in the wall treatment or its
  implementation, on the same grid with the same outer closure, numerics and forcing, both compared with one reference for
  a hydrodynamic quantity. 58 of 108 reports (54 of
  96; 54 of 104).
  3 more reports, 2 on either restricted basis, leave one of those controls unreported.
- Assumption tested on reference data alone: 17 reports (13;
  16).
- Test outside the data used for fitting: 33 reports and 110 tests. 9
  tests state that the target was withheld from training and model selection or apply unchanged coefficients published
  earlier by other authors, 60 compare variants of the treatment at the target or select with it, and
  41 remain unresolved. Excluding borderline reports: 102 tests in 29
  reports (9, 55, 38). Within the primary scope:
  100 in 30 (8, 53, 39).
- First extraction: all 115 reports, with the earlier record of each report at hand.
- Second extraction, made from the rules and the sources alone: a random 30 of the
  79 reports not used to write the rules (seed 2026111918), and every
  candidate report for the two rarer groups (44 and 43 reports). 74
  reports were extracted twice in all.
- A third extraction, with both at hand, reconciled each disagreement against the source.
- Agreement of the first and second extractions. Eligibility: 27 of the
  30 sampled reports and 64 of the
  74 extracted twice. Controlled comparison, random sample: κ = 0.87 (lower bound 0.67). Both
  disagreements concerned near-wall methods on grids that reach the viscous sublayer. Clarifications written after that
  test, before the reconciliation, keep such methods in scope and mark them as borderline. Assumption tested on reference
  data: κ = 0.67 (lower bound 0.44); the two extractions found 20 and 15 reports and both found
  the 13 that are not borderline. Test outside the fitting data: κ = 0.86 (lower bound 0.61). The
  lower bound is that of a 95 % bootstrap interval over reports.
- Criteria fixed in advance for quoting a count: κ of at least 0.60, a lower bound of at least 0.40, and a number of reports
  in the group that changes by no more than the larger of one and 15 % between the extractions. Two counts failed and are
  not quoted. A count restricted to a change of model, with the implementation unchanged, had κ = 0.86
  but 12 and 10 reports in the two extractions. Labels for
  comparisons of complete calculations did not reproduce (κ = 0.15).
- A further extraction, made once, completed the first-cell spacing of every coupled design and recorded the flow regime of
  every counted test. It added the fourth estimator to the borderline reports. 8 eligible reports state
  no first-cell distance in wall units.

## 6. Data extraction: which treatment is closer

- The rule is stored with the data (`data/revision/contrast_outcomes.json`, field `rule`). For every controlled comparison
  it records each quantity that the source compares with a reference for both treatments, under each condition, and which
  treatment lies closer. `code/derive_outcomes.py` derives every category from the recorded rows.
- A printed value decides a direction only if it holds for every value that rounds to the printed digits and against every
  reference given. On a plotted curve one treatment is closer if the two differ by more than the stroke width over more
  than half of the range and no resolved stretch favours the other. The order changes along the profile if each treatment
  is closer over at least one resolved stretch, whatever its length. Directions are resolved to printing or digitisation
  precision, not to sampling or reference uncertainty.
- 136 comparisons in 58 reports give 245 pairs of treatments and 981
  rows (900 plotted, 81 tabulated), with 55 thermal rows kept apart.
  The archived public copy of each report was used: an arXiv version for 37, the public copy
  served for the DOI for 18 and the publisher PDF for 3.
- Rule, sample and agreement thresholds were fixed before extraction. A second extraction covered a random
  20 of the 58 reports (seed 2026111914), 34 comparisons.
  Outcome of a comparison: same category for 33 of 34, κ = 0.94 (lower bound 0.76). Closer treatment per pair and class
  of quantity: same direction in 108 of 122, κ = 0.84 (lower bound 0.75). What distinguishes the two treatments:
  κ = 0.94 (lower bound 0.84). Which treatment is the designated baseline: κ = 0.88 (lower bound 0.70).
- A third extraction reconciled the 6 comparisons on which the two differed and changed the category of
  2. 102 of the
  136 comparisons were extracted once.
- For the 34 comparisons extracted twice, a separate extraction agreed on primary scope for
  all 34 and on first-cell class for 31.
- The rule does not say whether a drawn zero line marks a separation point, or which stroke counts when the reference is
  drawn thicker.
- Coded once: the factor that separates two conditions with opposite orders (`data/revision/level3_additions.json`) and
  the kind of flow, which follows the keyword rule in `code/outcome_structure.py`.
- Described after the categories were known, without changing any of them (`results/revision/outcome_structure.json`): the
  exclusive split of the 82 comparisons in which the order changes
  (55 only along one profile, 27 beyond one
  profile), the tabulation by number of resolved individual comparisons and the tabulation by kind of flow.
- An earlier set of 79 pairings, selected for heterogeneous results, is not used.

## 7. Synthesis and retrospective cases

- Quantities and references differ between reports. Directions are counted and no effect size is pooled. Reports that
  share a treatment, a computation or a benchmark are joined into 40 groups for the count by group
  (`data/revision/study_families.json`).
- The eight comparisons of Fig. 2 are a purposive choice across four groups of geometries. The search did not uniquely
  determine them.
- The five questions were applied twice, independently, to 13 retrospective cases (`data/checklist_cases.json`,
  `data/revision/checklist_choices.json`). Four cases had been used to write step 5, shared source papers link the 13 into
  nine groups, and outcomes were known when the cases were chosen.

## 8. Limits

- One index, journal articles in English, and reports with an open-access copy: 615 of the
  735 reports sought were not retrieved. The collection is not a census and its counts are not
  frequencies for the literature.
- 102 of 136 comparisons were extracted once.
- No source in the collection gives a joint interval for sampling, discretisation and reference uncertainty, so no
  direction is tested against such an interval.
