#!/usr/bin/env python3
"""Count every stage of the search, selection and data-extraction flow shown in Box 1.

Inputs: data/search_log.csv, data/search_records.csv, data/revision/search_flow.json (identification counts),
data/revision/retrieval_frame.csv, data/revision/source_dispositions.json, results/revision/derived_memberships.json,
results/revision/contrast_outcomes_summary.json, data/revision/agreement_v2.json.
Output: results/revision/flow_counts.json. Every count is recomputed from the records; the identification counts stored
in search_flow.json are checked against the search log and the screened records. Standard library only.
"""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, RESULTS = ROOT / "data", ROOT / "results/revision"


def table(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    log, screened = table(DATA / "search_log.csv"), table(DATA / "search_records.csv")
    stored = json.loads((DATA / "revision/search_flow.json").read_text())
    frame = table(DATA / "revision/retrieval_frame.csv")
    records = json.loads((DATA / "revision/source_dispositions.json").read_text())["records"]
    derived = json.loads((RESULTS / "derived_memberships.json").read_text())
    outcomes = json.loads((RESULTS / "contrast_outcomes_summary.json").read_text())["population"]
    agreement = json.loads((DATA / "revision/agreement_v2.json").read_text())

    identified = sum(int(r["records_retrieved"]) for r in log)
    removed = stored["removed_before_screening"]
    assert identified == stored["records_identified"] and len({r["strand"] for r in log}) == 4
    assert identified - stored["duplicates_removed"] - sum(removed.values()) == len(screened) == stored["records_screened"]

    screening = Counter(r["screening"] for r in frame)
    retrieval = Counter(r["retrieval"] for r in frame)
    obtained = [r for r in frame if r["retrieval"] == "retrieved"]
    flagged = [r for r in obtained if r["full_text_language_screen"] == "flagged"]
    set_aside = [r for r in flagged if not r["study_id"]]
    assessed = [r for r in obtained if r["study_id"]]
    check = stored["full_text_language_check"]
    assert len(flagged) == check["flagged"] and len(set_aside) == check["set_aside_without_assessment"]
    assert len(flagged) - len(set_aside) == check["assessed_despite_the_flag"]
    assert {r["study_id"] for r in assessed} == {r["study_id"] for r in records} and len(assessed) == len(records)
    assert all(r["full_text_language_screen"] == "pass" or r in flagged for r in obtained)

    status = Counter(r["eligibility_status"] for r in records)
    population = derived["population"]
    tiers = derived["matched_wall_treatment_change"]["tiers"]
    transfer = derived["transfer"]["all_counted_works"]
    sample = agreement["sample"]
    flow = dict(
        identification=dict(records_identified=identified, searches=4, duplicates_removed=stored["duplicates_removed"],
                            removed_before_screening=removed, removed_before_screening_total=sum(removed.values())),
        screening=dict(records_screened=len(screened), records_excluded=len(screened) - len(frame), reports_sought=len(frame),
                       sought_by_screening_decision=dict(screening)),
        retrieval=dict(reports_not_retrieved=len(frame) - len(obtained),
                       not_retrieved_by_reason={k: v for k, v in retrieval.items() if k != "retrieved"},
                       full_texts_obtained=len(obtained)),
        eligibility=dict(not_in_english_set_aside=len(set_aside), reports_assessed=len(assessed),
                         assessed_despite_language_flag=sorted(r["study_id"] for r in flagged if r["study_id"]),
                         excluded=status["excluded"], contested=status["contested"]),
        included=dict(eligible_reports=status["documented eligible design"],
                      borderline_reports=len(population["scope_boundary_works"]),
                      within_primary_scope=population["primary_scope"]["eligible_works_inside"]),
        evidence_groups=dict(
            controlled_comparison=dict(reports=tiers["broad"]["works"], comparisons=outcomes["contrasts"]),
            assumption_on_reference_data=dict(reports=derived["constitutive_constraint"]["works"]),
            test_outside_fitting_data=dict(reports=transfer["total_works"], tests=transfer["total_tests"])),
        second_extraction=dict(random_sample=len(sample["fresh_random_sample"]), sample_frame=len(sample["fresh_sample_frame"]),
                               reports_extracted_twice=len(sample["all_works_read_twice"])))
    assert flow["screening"]["records_excluded"] + flow["screening"]["reports_sought"] == flow["screening"]["records_screened"]
    assert flow["retrieval"]["reports_not_retrieved"] + flow["retrieval"]["full_texts_obtained"] == flow["screening"]["reports_sought"]
    assert flow["eligibility"]["not_in_english_set_aside"] + flow["eligibility"]["reports_assessed"] == flow["retrieval"]["full_texts_obtained"]
    assert flow["eligibility"]["excluded"] + flow["eligibility"]["contested"] + flow["included"]["eligible_reports"] == flow["eligibility"]["reports_assessed"]
    (RESULTS / "flow_counts.json").write_text(json.dumps(flow, indent=1) + "\n")
    print(json.dumps(flow, indent=1))


if __name__ == "__main__":
    main()
