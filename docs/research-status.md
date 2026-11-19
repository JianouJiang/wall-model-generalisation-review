# Current research status

The current manuscript is a corrected critical review prepared for expert feedback. It presents source-checked examples, a physical framework and a proposed checklist. It does not present the historical corpus as a settled quantitative analysis.

Completed corrections are documented in [scientific-corrections.md](scientific-corrections.md): source/version reconciliation for retained cases, explicit physical-scope uncertainty, separation of relative and absolute error, withdrawal of unsupported aggregates, and a limited interpretation of retrospective checklist records.

The source reassessment traces every retrieved work. For the standard periodic hill at bulk Reynolds number 10,595, five studies tabulate separation and reattachment against a reference for both crossings. A direction of change is called resolved when it holds for every value that rounds to the printed digits and against every reference in the table. Of the nine fixed-mesh wall-treatment comparisons, five move both crossings closer, two move them in opposite directions to the printed digits, one is unresolved (a one-decimal baseline and a reference-dependent reattachment change) and one has no baseline bubble. Of the two opposite cases, one source does not report its averaging interval and the other averaged its two runs over about 15 and 19 flow-through times. Neither reports a sampling uncertainty for a crossing. The data file keeps the second in a class of its own (`controls differ`) to record the different intervals. Ranking the point values alone gives five, three and one. In each of the three nominally opposite cases the smaller change is at most 0.05 hill heights. The studies reuse meshes, measurements and trained treatments. These tables do not establish a trade-off between the two crossings. [Printed digits and editions](../data/revision/table_digits.json) · [Resolved directions](../results/revision/direction_resolution.json) · [Point-value results](../results/revision/paired_error_changes.json) · [Source tables](../data/revision/hill_table_population.json)

Three group counts are quoted in the paper and rest on recorded facts. Rules fixed in advance say which facts to record for a wall-treatment contrast, a constitutive test and a transfer test, and a script derives every membership. A first automated reading applied the rules to all 115 works with the earlier record in view. A second, given only the rules and the sources, read a seeded random 30 of the 79 works that had not been read twice before, and every candidate for the constitutive and transfer groups (74 works in all). A third reading, which saw both, settled each disagreement against the source with quotations. After settlement 108 works are eligible, two are contested and five are excluded.

- **Matched wall-treatment contrast.** 58 of 108 eligible works contain two coupled calculations that differ only in the wall treatment or its implementation and are compared with one quantitative reference for a hydrodynamic quantity; 61 if an unreported control is allowed. On the random sample Cohen's κ is 0.87 (lower 95 % bound 0.67). The count restricted to a change of model (50) is **not quotable**: its member count on the random sample changed from 12 to 10, more than the limit fixed in advance.
- **Scope boundary.** Both disagreements on the random sample concern near-wall methods on grids that reach the viscous sublayer, for which two rule texts gave different dispositions. Three clarifications were written after the agreement test and before the third reading. Eleven eligible works are marked as boundary cases (five sublayer-resolving methods, three stress estimators never presented as wall models, three with disputed eligibility). Without them the counts are 54 of 97 and 56 of 97.
- **Constitutive constraint.** 17 works (14 without boundary cases); κ 0.67 (lower bound 0.44) over the 44 candidate works.
- **Transfer.** 33 works test a fitted treatment at 110 conditions outside its fitting set. Nine tests are qualified by a hold-out statement or by coefficients frozen by other authors (six in one study), 60 are partly exposed and 41 are unresolved. Whether a work has such a test: κ 0.86 (lower bound 0.61).
- **Not reproduced.** The complete-system benchmark label (κ 0.15) and the coupled-LES label (member count 19 against 16). No count is quoted for either. A second automated reading of 34 of the 79 earlier pairings, which received the first reading's quantities and locations, agreed on whether two quantities came from the same pair of runs in 31 of 34 and on the finer category in 12 of 24.

All readings are automated; none is a human screening. [Agreement record, settlement and decisions](../data/revision/agreement_v2.json) · [Derived memberships](../results/revision/derived_memberships.json) · [Recomputed statistics](../results/revision/agreement_check.json) · [Membership changes and their causes](../data/revision/membership_changes.json) · [Pairings](../data/revision/reader_agreement.json)

## Limits of the current work

- The collection is not exhaustive and its historical coding is not a certified census of current journal versions.
- Identified preprints are used as preprints; journal equivalence is not assumed.
- The framework is not an exhaustive or mutually exclusive causal taxonomy.
- Retrospective proposal agreement does not validate the checklist's predictive value.
- Absolute accuracy requires a relevant reference and uncertainty assessment; sensitivity alone cannot supply it.
- Resolved directions are resolved to printed digits. Sampling, discretisation and measurement uncertainties enter only where a source reports them.
- The third reading saw both earlier readings. It is not blind, and the first reading saw the earlier record. Agreement describes how reproducibly facts are assigned inside this collection, not whether the collection represents the literature.
- 41 works were read once under the fact rules. The 17 of them that hold a member contrast had every member contrast checked against the source by the third reading. A comparison made only by statement (clarification S3) could be found only in the 74 works read twice.
- The screen for sublayer-resolving methods used terms in the readings' records, not the full texts.
- The description of why the other 50 eligible works hold no matched contrast was not tested for agreement.
- The journal tables of Krank and Wall (2016) and Zhou and Bae (2024) were not accessible. Their values come from the preprints named in the reference list; the first was also checked against the first author's dissertation.

The present scientific claims stand on their stated evidence and limitations. Reproduction checks do not constitute independent scientific replication or journal review.

## Correspondence and submission

The owner controls sending and repository visibility. Expert correspondence requires the owner's specified confidentiality arrangements and current verification of each recipient address. No expert email or journal submission is authorised by this file. Journal submission also requires final authorship and restoration of the disclosure text held separately by the owner.
