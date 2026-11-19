"""Recompute the agreement between two readings and the decisions that follow from the thresholds fixed in advance.

Input: data/revision/agreement_v2.json (labels of both readings for every work read twice, the settlement of every
disagreement and the decisions) and results/revision/derived_memberships.json. Cohen's kappa, the member counts and the
percentile bootstrap bounds (10,000 resamples of works, seed stored in the file) are recomputed from the per-work
labels and must equal the stored values. A count is quotable only if kappa >= 0.60, the lower 95 % bound >= 0.40, the
member count changes by at most max(1, 15 %) where that criterion applies, and every disagreement has a settled,
attributed answer. Output: results/revision/agreement_check.json. Needs numpy (python3 -I).
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TIERS = ("strict", "broad", "upper")
FIVE = ("prescribed_input", "coupled_wmles", "rans_comparison", "system_benchmark", "thermal")


def kappa(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    po = np.mean(a == b)
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return float("nan") if pe == 1 else float((po - pe) / (1 - pe))


def recompute(a, b, rng, resamples=10000):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    index = rng.integers(0, len(a), size=(resamples, len(a)))
    values = np.array([kappa(a[i], b[i]) for i in index])
    values = values[~np.isnan(values)]
    return dict(both=int((a & b).sum()), first_only=int((a & ~b).sum()), second_only=int((~a & b).sum()), neither=int((~a & ~b).sum()),
                kappa=kappa(a, b), members_first=int(a.sum()), members_second=int(b.sum()),
                kappa_bootstrap_95=[float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))] if len(values) else None)


def same(new, stored, name):
    for key, value in new.items():
        old = stored[key]
        if isinstance(value, float):
            assert (np.isnan(value) and old != old) or abs(value - old) < 1e-12, (name, key, value, old)
        elif isinstance(value, list):
            assert all(abs(x - y) < 1e-12 for x, y in zip(value, old)), (name, key, value, old)
        else:
            assert value == old, (name, key, value, old)


def main():
    data = json.loads((ROOT / "data/revision/agreement_v2.json").read_text())
    derived = json.loads((ROOT / "results/revision/derived_memberships.json").read_text())
    work = {w["study_id"]: w for w in data["per_work"]}
    sample, stored, decisions = data["sample"], data["statistics"], data["decisions"]
    assert len(sample["fresh_random_sample"]) == 30 and len(sample["all_works_read_twice"]) == len(work) == 74
    assert len(sample["works_without_a_second_reading"]) == 115 - 74
    # The random sample is redrawn from its frame: the 79 works that had not been read twice before, in two strata.
    strata, draw = sample["frame_strata"], sample["draw"]
    assert len(sample["works_read_twice_on_19_november"]) == 36 and len(sample["fresh_sample_frame"]) == 79
    assert not set(sample["fresh_sample_frame"]) & set(sample["works_read_twice_on_19_november"])
    generator = np.random.default_rng(draw["seed"])
    redrawn = [generator.choice(sorted(strata[k]), draw["picks"][k], replace=False).tolist() for k in ("historical_cohort", "other")]
    assert sorted(redrawn[0] + redrawn[1]) == sorted(sample["fresh_random_sample"]), "the sample is not the seeded draw"

    def labels(ids, key):
        return [work[i]["first"][key] for i in ids], [work[i]["second"][key] for i in ids]

    seed = data["protocol"]["seed"]
    rng = np.random.default_rng(seed)
    fresh = {}
    for key in TIERS + FIVE + ("eligible",):          # the order in which the stored bounds were drawn
        fresh[key] = recompute(*labels(sample["fresh_random_sample"], key), rng)
        same(fresh[key], stored["fresh_random_sample"][key], key)
    rng = np.random.default_rng(seed)
    pool = {}
    for key in ("constitutive", "fact_i", "fact_ii", "fact_iii"):
        pool[key] = recompute(*labels(sample["constitutive_pool"], key), rng)
        same(pool[key], stored["constitutive_pool"][key], key)
    for key in ("has_transfer", "fitted"):
        pool[key] = recompute(*labels(sample["transfer_pool"], key), rng)
        same(pool[key], stored["transfer_pool"][key], key)

    def criteria(st, member_change=True):
        out = [st["kappa"] >= 0.60, st["kappa_bootstrap_95"][0] >= 0.40]
        if member_change:
            out.append(abs(st["members_second"] - st["members_first"]) <= max(1, 0.15 * st["members_first"]))
        return all(out)

    settled = {(i["study_id"], i["question"]) for i in data["settlement"]["items"] if i["attribution"] and i["quotes"]}
    report = {}
    for key in TIERS + FIVE:
        d = decisions[key]
        assert d["statistical_criteria_met"] == criteria(fresh[key]), key
        if key in TIERS:
            disputed = [i for i in sample["all_works_read_twice"] if key in work[i]["disagreements"]]
            assert all((i, "scope") in settled or (i, "contrasts") in settled for i in disputed), (key, disputed)
            assert d["quotable"] == (d["statistical_criteria_met"] and d["every_disagreement_settled"]), key
            tier = derived["matched_wall_treatment_change"]["tiers"][key]
            assert (d["settled_works"], d["settled_works_without_scope_boundary"]) == (tier["works"], tier["works_without_scope_boundary"]), key
        else:
            assert d["quotable"] == d["statistical_criteria_met"], key
        report[key] = dict(kappa=round(fresh[key]["kappa"], 3), lower_95=round(fresh[key]["kappa_bootstrap_95"][0], 3),
                           members=[fresh[key]["members_first"], fresh[key]["members_second"]], quotable=d["quotable"])
    d = decisions["constitutive_constraint"]
    assert d["statistical_criteria_met"] == criteria(pool["constitutive"], member_change=False)
    disputed = [i for i in sample["constitutive_pool"] if work[i]["first"]["constitutive"] != work[i]["second"]["constitutive"]]
    assert all((i, "constitutive") in settled or (i, "scope") in settled for i in disputed), disputed
    assert d["quotable"] == (d["statistical_criteria_met"] and d["every_disagreement_settled"])
    assert d["settled_works"] == derived["constitutive_constraint"]["works"] and d["members"] == derived["constitutive_constraint"]["members"]
    report["constitutive_constraint"] = dict(kappa=round(pool["constitutive"]["kappa"], 3), lower_95=round(pool["constitutive"]["kappa_bootstrap_95"][0], 3),
                                             members=[pool["constitutive"]["members_first"], pool["constitutive"]["members_second"]], quotable=d["quotable"])
    d = decisions["transfer"]
    rows = stored["transfer_matched_rows"]
    assert d["statistical_criteria_met"] == (criteria(pool["has_transfer"], member_change=False) and rows["status_kappa"] >= 0.60)
    assert d["quotable"] == (d["statistical_criteria_met"] and d["every_disagreement_settled"])
    whole = derived["transfer"]["all_counted_works"]
    assert d["settled_split_of_tests"] == whole["tests"] and d["tests_not_shown_to_be_exposed"] == whole["tests_not_shown_to_be_exposed"]
    report["transfer"] = dict(kappa_has_a_row=round(pool["has_transfer"]["kappa"], 3), lower_95=round(pool["has_transfer"]["kappa_bootstrap_95"][0], 3),
                              status_kappa_matched_rows=round(rows["status_kappa"], 3), quotable=d["quotable"], split_of_tests=whole["tests"])
    both = [i for i in sample["fresh_random_sample"] if work[i]["first"]["eligible"] and work[i]["second"]["eligible"]]
    report["fresh_works_both_readings_call_eligible"] = dict(
        works=len(both), tiers_agree=sum(all(work[i]["first"][t] == work[i]["second"][t] for t in TIERS) for i in both))
    assert decisions["strict"]["quotable"] is False or criteria(fresh["strict"])
    (ROOT / "results/revision/agreement_check.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Agreement and decisions recomputed:", {k: v["quotable"] for k, v in report.items() if "quotable" in v})


if __name__ == "__main__":
    main()
