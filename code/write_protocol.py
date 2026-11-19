#!/usr/bin/env python3
"""Write docs/protocol.md and docs/contributing-reports.md from the data and the derived results.

The protocol states the search, screening, eligibility assessment, data extraction and agreement behind Box 1 and the
Methods of the Review. Every number in it is formatted here from a data or result file, so the document cannot drift
from the record. Standard library only. Run after derive_memberships.py, check_agreement.py, derive_outcomes.py,
outcome_structure.py and flow_counts.py (code/reproduce.py does this).
"""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, REV, RES = ROOT / "data", ROOT / "data/revision", ROOT / "results/revision"


def load(path):
    return json.loads(path.read_text())


def n(value):
    return f"{value:,}"


def ids(values):
    return ", ".join(sorted(values))


def kappa(s):
    return f"κ = {s['kappa']:.2f} (lower bound {s['kappa_bootstrap_95'][0]:.2f})"


def protocol():
    search, flow, flow_in = load(DATA / "search_protocol.json"), load(RES / "flow_counts.json"), load(REV / "search_flow.json")
    derived, agreement = load(RES / "derived_memberships.json"), load(REV / "agreement_v2.json")
    out, twice = load(RES / "contrast_outcomes_summary.json"), load(REV / "outcome_agreement.json")
    structure, paired = load(RES / "outcome_structure.json"), load(REV / "paired_readings.json")["records"]
    ident, scr, ret, eli, inc = flow["identification"], flow["screening"], flow["retrieval"], flow["eligibility"], flow["included"]
    why, sought = ret["not_retrieved_by_reason"], scr["sought_by_screening_decision"]
    removed = ident["removed_before_screening"]
    lang = flow_in["full_text_language_check"]
    pop, scope = derived["population"], derived["population"]["primary_scope"]
    kinds, boundary = pop["scope_boundary_by_kind"], {b["study_id"]: b["kind"] for b in agreement["settlement"]["scope_boundary"]}
    boundary.update({a["study_id"]: a["kind"] for a in agreement["fourth_reading"]["scope_boundary_added"]})
    by_kind = {k: sorted(i for i, v in boundary.items() if v == k) for k in kinds}
    assert sorted(boundary) == sorted(pop["scope_boundary_works"]) and all(len(by_kind[k]) == kinds[k] for k in kinds)
    tiers = derived["matched_wall_treatment_change"]["tiers"]
    broad, upper, strict = tiers["broad"], tiers["upper"], tiers["strict"]
    const, transfer = derived["constitutive_constraint"], derived["transfer"]
    whole, without, within = transfer["all_counted_works"], transfer["without_scope_boundary"], transfer["in_primary_scope"]
    q, pe, un = "qualified", "partly exposed", "selection unresolved"
    stats, sample, decisions = agreement["statistics"], agreement["sample"], agreement["decisions"]
    work = {w["study_id"]: w for w in agreement["per_work"]}
    same = lambda group: sum(work[i]["first"]["disposition"] == work[i]["second"]["disposition"] for i in group)
    fresh, pool_c, pool_t = stats["fresh_random_sample"], stats["constitutive_pool"]["constitutive"], stats["transfer_pool"]["has_transfer"]
    status = Counter(r["eligibility_status"] for r in load(REV / "source_dispositions.json")["records"])
    first_cell = pop["first_cell_class_of_eligible_works"]
    o_pop, o_stats = out["population"], out["agreement"]["statistics"]
    s1, s2 = o_stats["S1_contrast_category"], o_stats["S2_direction_by_pair_and_class"]
    editions = o_pop["works_by_edition_read"]
    settled = twice["settlement"]
    queries = "\n".join(f"  - {x['id']}: {x['label']}" for x in search["queries"])
    filters = "\n".join(f"  - {x['rule']}" for x in search["filters_after_retrieval"])
    more = upper["works"] - broad["works"]
    more_restricted = {upper[k] - broad[k] for k in ("works_without_scope_boundary", "works_in_primary_scope")}
    assert len(more_restricted) == 1
    text = f"""# Search, selection and data-extraction protocol

This document accompanies Box 1 and the Methods of the Review. `code/write_protocol.py` formats every number below from
the data file named beside it. Stage names follow the PRISMA 2020 flow diagram (Page et al., BMJ 372, n71, 2021). The
search is reported item by item as PRISMA-S asks (Rethlefsen et al., Syst. Rev. 10, 39, 2021). The synthesis counts
directions and pools no effect sizes (Campbell et al., BMJ 368, l6890, 2020). The protocol was not registered.

## 1. Search

- Database and platform: {search['engine']['name']}, works endpoint (`{search['engine']['endpoint']}`), field
  `{search['engine']['field']}`. One index was searched. No trial registry, website, citation search, contact with authors
  or other method contributed records to the collection.
- Full search strategies, exactly as run, are in `data/search_protocol.json`. Each request, its date and the number of
  records returned are in `data/search_log.csv` (fetched on 17 November 2026).
{queries}
- Limits: publication dates {search['date_window']['from']} to {search['date_window']['to']}. Filters applied to the
  retrieved records:
{filters}
- No published search filter was used. No earlier strategy was reused, the search was not updated, and the strategy was
  not peer reviewed.
- Records identified: {n(ident['records_identified'])} from {ident['searches']} searches.
- Deduplication: {search['deduplication']} {n(ident['duplicates_removed'])} duplicates were removed.
- Removed before screening: {n(removed['not a journal article (OpenAlex type)'])} not journal articles,
  {removed['primary source not a journal']} with a primary source that is not a journal and {removed['language not English']}
  not in English ({n(ident['removed_before_screening_total'])} in all). Source: `data/revision/search_flow.json`.

## 2. Screening on title and abstract

- {n(scr['records_screened'])} records were screened against criteria T1 to T3 of `data/search_protocol.json`
  ({flow_in['records_screened_without_an_abstract']} had no abstract in the index). Each record was screened as include,
  exclude or unclear. {n(scr['records_excluded'])} were excluded.
- {scr['reports_sought']} reports were sought: {sought['include']} screened as include, {sought['unclear']} as unclear and
  {sought['forward (dual disagreement)']} on which two screenings disagreed. Source: `data/search_records.csv`.

## 3. Retrieval

- {scr['reports_sought'] - why['no candidate route']} of the {scr['reports_sought']} reports had a candidate open-access route and
  {why['no candidate route']} had none. {why['access refused']} routes refused access and {why['unusable retrieval']} returned an
  unusable file. {ret['full_texts_obtained']} full texts were obtained. No paywall was circumvented. Source:
  `data/revision/retrieval_frame.csv`.
- Language check on the full text. {lang['rule']} {lang['flagged']} texts were flagged. {lang['set_aside_without_assessment']} were
  set aside without assessment. {lang['assessed_despite_the_flag']} ({ids(eli['assessed_despite_language_flag'])}) had been entered
  before the check was applied to every text and were assessed from their equations, figures, tables and English abstracts.

## 4. Eligibility

- {eli['reports_assessed']} reports were assessed in full text. An eligible report names a wall treatment or wall-stress
  estimator and contains an identifiable test that compares a quantity with a reference. Editions of one work count once.
  {inc['eligible_reports']} reports are eligible, {status['contested']} are contested and {status['excluded']} are excluded.
  Source: `data/revision/source_dispositions.json`.
- Primary scope: turbulent flow of a single-phase Newtonian fluid with constant properties and no buoyancy over smooth
  walls at Mach numbers up to 0.3. Of the {scope['recorded_tests']} recorded tests, {scope['recorded_tests_outside']} lie
  outside it and {scope['recorded_tests_with_compressibility_not_stated']} state neither a Mach number nor compressibility and
  count as inside it. {len(scope['eligible_works_wholly_outside'])} eligible reports test only flows outside the primary scope
  ({ids(scope['eligible_works_wholly_outside'])}), which leaves {scope['eligible_works_inside']} within it. Source:
  `data/revision/regime_facts.json`.
- Borderline reports ({len(boundary)}). {kinds['sublayer-resolving near-wall method']} use near-wall methods on grids that reach the
  viscous sublayer ({ids(by_kind['sublayer-resolving near-wall method'])}).
  {kinds['estimator not presented as a wall model']} test stress estimators never presented as wall models
  ({ids(by_kind['estimator not presented as a wall model'])}).
  {kinds['eligibility disputed between the readings on a rule ambiguity']} had eligibility disputed between the two extractions
  ({ids(by_kind['eligibility disputed between the readings on a rule ambiguity'])}).
- Counts are given on three bases: the collection; excluding borderline reports and comparisons on grids that reach the
  sublayer ({ids(pop['contrasts_on_a_sublayer_resolving_grid'])}); and within the primary scope. The eligible reports number
  {inc['eligible_reports']}, {pop['eligible_works_without_scope_boundary']} and {scope['eligible_works_inside']} on the three bases.

## 5. Data extraction: the three groups of evidence

- Rules fixed before extraction name the facts that define each group (`data/revision/wall_change_contrasts.json` stores the
  rule text). `code/derive_memberships.py` derives each group from the extracted facts. No group label is typed by hand.
- Controlled comparison of wall treatments: two coupled calculations that differ only in the wall treatment or its
  implementation, on the same grid with the same outer closure, numerics and forcing, both compared with one reference for
  a hydrodynamic quantity. {broad['works']} of {inc['eligible_reports']} reports ({broad['works_without_scope_boundary']} of
  {pop['eligible_works_without_scope_boundary']}; {broad['works_in_primary_scope']} of {scope['eligible_works_inside']}).
  {more} more reports, {more_restricted.pop()} on either restricted basis, leave one of those controls unreported.
- Assumption tested on reference data alone: {const['works']} reports ({const['works_without_scope_boundary']};
  {const['works_in_primary_scope']}).
- Test outside the data used for fitting: {whole['total_works']} reports and {whole['total_tests']} tests. {whole['tests'][q]}
  tests state that the target was withheld from training and model selection or apply unchanged coefficients published
  earlier by other authors, {whole['tests'][pe]} compare variants of the treatment at the target or select with it, and
  {whole['tests'][un]} remain unresolved. Excluding borderline reports: {without['total_tests']} tests in {without['total_works']}
  reports ({without['tests'][q]}, {without['tests'][pe]}, {without['tests'][un]}). Within the primary scope:
  {within['total_tests']} in {within['total_works']} ({within['tests'][q]}, {within['tests'][pe]}, {within['tests'][un]}).
- First extraction: all {eli['reports_assessed']} reports, with the earlier record of each report at hand.
- Second extraction, made from the rules and the sources alone: a random {len(sample['fresh_random_sample'])} of the
  {len(sample['fresh_sample_frame'])} reports not used to write the rules (seed {agreement['protocol']['seed']}), and every
  candidate report for the two rarer groups ({pool_c['n']} and {pool_t['n']} reports). {len(sample['all_works_read_twice'])}
  reports were extracted twice in all.
- A third extraction, with both at hand, reconciled each disagreement against the source.
- Agreement of the first and second extractions. Eligibility: {same(sample['fresh_random_sample'])} of the
  {len(sample['fresh_random_sample'])} sampled reports and {same(sample['all_works_read_twice'])} of the
  {len(sample['all_works_read_twice'])} extracted twice. Controlled comparison, random sample: {kappa(fresh['broad'])}. Both
  disagreements concerned near-wall methods on grids that reach the viscous sublayer. Clarifications written after that
  test, before the reconciliation, keep such methods in scope and mark them as borderline. Assumption tested on reference
  data: {kappa(pool_c)}; the two extractions found {pool_c['members_first']} and {pool_c['members_second']} reports and both found
  the {const['works_without_scope_boundary']} that are not borderline. Test outside the fitting data: {kappa(pool_t)}. The
  lower bound is that of a 95 % bootstrap interval over reports.
- Criteria fixed in advance for quoting a count: κ of at least 0.60, a lower bound of at least 0.40, and a number of reports
  in the group that changes by no more than the larger of one and 15 % between the extractions. Two counts failed and are
  not quoted. A count restricted to a change of model, with the implementation unchanged, had κ = {fresh['strict']['kappa']:.2f}
  but {fresh['strict']['members_first']} and {fresh['strict']['members_second']} reports in the two extractions. Labels for
  comparisons of complete calculations did not reproduce (κ = {fresh['system_benchmark']['kappa']:.2f}).
- A further extraction, made once, completed the first-cell spacing of every coupled design and recorded the flow regime of
  every counted test. It added the fourth estimator to the borderline reports. {first_cell['not stated']} eligible reports state
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
- {o_pop['contrasts']} comparisons in {o_pop['works']} reports give {o_pop['pairs']} pairs of treatments and {o_pop['rows']}
  rows ({o_pop['plotted_rows']} plotted, {o_pop['tabulated_rows']} tabulated), with {o_pop['heat_rows']} thermal rows kept apart.
  The archived public copy of each report was used: an arXiv version for {editions['arXiv version']}, the public copy
  served for the DOI for {editions['public copy served for the DOI']} and the publisher PDF for {editions['publisher PDF']}.
- Rule, sample and agreement thresholds were fixed before extraction. A second extraction covered a random
  {len(twice['sample']['works'])} of the {o_pop['works']} reports (seed {twice['sample']['seed']}), {s1['n']} comparisons.
  Outcome of a comparison: same category for {s1['agree']} of {s1['n']}, {kappa(s1)}. Closer treatment per pair and class
  of quantity: same direction in {s2['agree']} of {s2['n']}, {kappa(s2)}. What distinguishes the two treatments:
  {kappa(o_stats['S4_theme'])}. Which treatment is the designated baseline: {kappa(o_stats['S5_baseline_role'])}.
- A third extraction reconciled the {settled['settled']} comparisons on which the two differed and changed the category of
  {settled['contrast_category']['changed_from_first_among_all_settled']}. {o_pop['contrasts'] - o_stats['contrasts']} of the
  {o_pop['contrasts']} comparisons were extracted once.
- For the {o_stats['S6_primary_scope']['n']} comparisons extracted twice, a separate extraction agreed on primary scope for
  all {o_stats['S6_primary_scope']['agree']} and on first-cell class for {o_stats['S6_first_cell_class']['agree']}.
- The rule does not say whether a drawn zero line marks a separation point, or which stroke counts when the reference is
  drawn thicker.
- Coded once: the factor that separates two conditions with opposite orders (`data/revision/level3_additions.json`) and
  the kind of flow, which follows the keyword rule in `code/outcome_structure.py`.
- Described after the categories were known, without changing any of them (`results/revision/outcome_structure.json`): the
  exclusive split of the {structure['order_changes']} comparisons in which the order changes
  ({structure['exclusive_outcome']['along one profile only']} only along one profile, {structure['beyond_one_profile']} beyond one
  profile), the tabulation by number of resolved individual comparisons and the tabulation by kind of flow.
- An earlier set of {len(paired)} pairings, selected for heterogeneous results, is not used.

## 7. Synthesis and retrospective cases

- Quantities and references differ between reports. Directions are counted and no effect size is pooled. Reports that
  share a treatment, a computation or a benchmark are joined into {o_pop['families']} groups for the count by group
  (`data/revision/study_families.json`).
- The eight comparisons of Fig. 2 are a purposive choice across four groups of geometries. The search did not uniquely
  determine them.
- The five questions were applied twice, independently, to 13 retrospective cases (`data/checklist_cases.json`,
  `data/revision/checklist_choices.json`). Four cases had been used to write step 5, shared source papers link the 13 into
  nine groups, and outcomes were known when the cases were chosen.

## 8. Limits

- One index, journal articles in English, and reports with an open-access copy: {ret['reports_not_retrieved']} of the
  {scr['reports_sought']} reports sought were not retrieved. The collection is not a census and its counts are not
  frequencies for the literature.
- {o_pop['contrasts'] - o_stats['contrasts']} of {o_pop['contrasts']} comparisons were extracted once.
- No source in the collection gives a joint interval for sampling, discretisation and reference uncertainty, so no
  direction is tested against such an interval.
"""
    return text


def contributing_reports():
    out = load(RES / "contrast_outcomes_summary.json")
    structure = {r["contrast_id"]: r for r in load(RES / "outcome_structure.json")["per_contrast"]}
    with (DATA / "studies.csv").open(newline="") as stream:
        study = {r["study_id"]: r for r in csv.DictReader(stream)}
    by_report = {}
    for d in out["per_contrast"]:
        by_report.setdefault(d["study_id"], []).append(d["contrast_id"])
    lines = ["# Reports that contribute controlled comparisons",
             "",
             f"The {len(out['per_contrast'])} controlled comparisons of the Review come from these {len(by_report)} reports. "
             "`code/write_protocol.py` writes this list from `data/studies.csv` and `results/revision/outcome_structure.json`. "
             "The outcome is one of: along one profile only, between conditions, between quantities only, between two quantities "
             "of one class only, one order, nothing resolved. The number in brackets is the number of resolved individual comparisons.",
             "",
             "| Report | First author, year, journal | DOI | Comparisons and outcomes |",
             "|---|---|---|---|"]
    for sid in sorted(by_report):
        s = study[sid]
        cells = "; ".join(f"{c} {structure[c]['outcome']} [{structure[c]['resolved_comparisons']}]" for c in sorted(by_report[sid]))
        lines.append(f"| {sid} | {s['first_author']}, {s['year']}, {s['source']} | [{s['doi']}](https://doi.org/{s['doi']}) | {cells} |")
    return "\n".join(lines) + "\n"


def main():
    docs = ROOT / "docs"
    (docs / "protocol.md").write_text(protocol())
    (docs / "contributing-reports.md").write_text(contributing_reports())
    print("written docs/protocol.md and docs/contributing-reports.md")


if __name__ == "__main__":
    main()
