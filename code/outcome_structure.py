#!/usr/bin/env python3
"""Descriptive structure of the order-of-treatments record: where the order changes, and how the result depends on how
much a source reports and on the kind of flow.

Inputs: results/revision/contrast_outcomes_summary.json (categories derived by derive_outcomes.py under the rule fixed
before data extraction) and data/revision/wall_change_contrasts.json (the recorded case description of each contrast).
Output: results/revision/outcome_structure.json.

Everything here was added after the categories were known. Nothing changes a category, a count or the rule. The splits
are exclusive regroupings of the recorded places of change; the bins of resolved comparisons (1-2, 3-5, 6-10, more
than 10) were chosen before the tabulation was run; the kind of flow is assigned by the keyword rule below from the
recorded case description and was not extracted a second time. Standard library only.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINS = (("1-2", 1, 2), ("3-5", 3, 5), ("6-10", 6, 10), ("more than 10", 11, 10**9))

# Kind of flow, from the recorded case description. The first matching rule applies.
# "developed" = statistically stationary plane channel, half-channel or pipe with a mean flow in one direction, and the
# zero-pressure-gradient flat-plate boundary layer: the flows for which equilibrium wall laws are calibrated.
FLOW_RULES = (
    ("flow with separation, streamwise pressure gradient, three-dimensionality, roughness or rotation",
     r"hill|step|bump|diffuser|hump|NACA|blade|vane|cascade|separation bubble|Juncture|CRM|cyclist|wavy wall|impinging jet|"
     r"rod bundle|heat exchanger|RVACS|drip-irrigation|bent square duct|Poiseuille-Couette|strips|roughness|rough-wall|rotation"),
    ("developed flow with unsteady or transverse forcing",
     r"sudden|pulsating|accelerating|imposed constant adverse pressure gradient|spanwise pressure gradient"),
    ("developed channel, pipe or flat-plate boundary layer",
     r"channel|pipe|parallel plates|flat[- ]plate|ZPG|zero-pressure-gradient"),
)


def flow_kind(case):
    for name, pattern in FLOW_RULES:
        if re.search(pattern, case, re.I):
            return name
    raise ValueError(f"no rule for: {case}")


def kind_of_outcome(d):
    """Exclusive place of the outcome of one contrast."""
    if d["category"] != "order changes":
        return d["category"]
    where = set(d["where"])
    if where == {"within a profile"}:
        return "along one profile only"
    if "between conditions" in where:
        return "between conditions"
    if "between quantities" in where:
        return "between quantities only"
    return "between two quantities of one class only"


def main():
    out = json.loads((ROOT / "results/revision/contrast_outcomes_summary.json").read_text())
    cases = {r["contrast_id"]: r["case"] for r in json.loads((ROOT / "data/revision/wall_change_contrasts.json").read_text())["records"]}
    per = out["per_contrast"]
    resolved = {d["contrast_id"]: sum(p["cells"] - p["cells_unresolved"] for p in d["pairs"]) for d in per}
    kind = {d["contrast_id"]: kind_of_outcome(d) for d in per}
    flow = {d["contrast_id"]: flow_kind(cases[d["contrast_id"]]) for d in per}
    order = ("along one profile only", "between conditions", "between quantities only", "between two quantities of one class only",
             "one order", "nothing resolved")
    places = Counter(kind.values())
    beyond = [i for i, k in kind.items() if k in order[1:4]]
    changes = [i for i, k in kind.items() if k in order[:4]]

    # Category against the number of resolved comparisons (pairs of treatments by row and condition).
    by_bin = []
    for label, low, high in BINS:
        ids = [i for i, n in resolved.items() if low <= n <= high]
        by_bin.append(dict(resolved_comparisons=label, contrasts=len(ids),
                           order_changes=sum(i in changes for i in ids), beyond_one_profile=sum(i in beyond for i in ids),
                           along_one_profile_only=sum(kind[i] == "along one profile only" for i in ids),
                           one_order=sum(kind[i] == "one order" for i in ids)))
    none = [i for i, n in resolved.items() if n == 0]
    assert all(kind[i] == "nothing resolved" for i in none) and len(none) == places["nothing resolved"]
    one_order = [i for i, k in kind.items() if k == "one order"]

    # Resolved comparisons per pair of treatments, by what distinguishes the two.
    per_pair = defaultdict(list)
    for d in per:
        for p in d["pairs"]:
            per_pair[p["theme"]].append(p["cells"] - p["cells_unresolved"])
    pairs = {t: dict(pairs=len(v), resolved_comparisons=sum(v), mean_per_pair=round(sum(v) / len(v), 2)) for t, v in sorted(per_pair.items())}

    # The same exclusive split for pairs of treatments, by what distinguishes the two.
    def pair_kind(p):
        if p["category"] != "order changes":
            return "one order" if p["category"] == "one order" else "nothing resolved"
        return "along one profile only" if set(p["where"]) == {"within a profile"} else "beyond one profile"
    pair_split = defaultdict(Counter)
    for d in per:
        for p in d["pairs"]:
            pair_split[p["theme"]][pair_kind(p)] += 1
            pair_split["all pairs"][pair_kind(p)] += 1
    pair_order = ("along one profile only", "beyond one profile", "one order", "nothing resolved")
    pairs_exclusive = {t: dict(pairs=sum(c.values()), **{k: c[k] for k in pair_order}) for t, c in sorted(pair_split.items())}

    # Separating factor of the changes between conditions (coded once, data/revision/level3_additions.json), by kind of flow.
    coded = json.loads((ROOT / "data/revision/level3_additions.json").read_text())["condition_factors"]["contrasts"]
    factor_by_flow = defaultdict(Counter)
    for cid, entries in coded.items():
        for name in {e["factor"] for e in entries}:
            factor_by_flow[flow[cid]][name] += 1

    # Pairs in which one treatment has the closer separation or reattachment point: the wall-stress order of the same pair.
    crossing = [p["direction_by_class"] for d in per for p in d["pairs"] if p["direction_by_class"].get("separation") in ("first", "other")]
    with_stress = [c["wall_stress"] for c in crossing if "wall_stress" in c]
    crossing_and_stress = dict(pairs_with_one_treatment_closer_on_crossing_points=len(crossing), of_which_wall_stress_compared=len(with_stress),
                               wall_stress_order_changes=sum(v == "changes" for v in with_stress),
                               wall_stress_one_order=sum(v in ("first", "other") for v in with_stress),
                               wall_stress_unresolved=sum(v == "unresolved" for v in with_stress))

    themes_beyond = Counter(t for d in per if d["contrast_id"] in beyond for t in d["themes"])
    by_flow = {}
    for name, _ in FLOW_RULES:
        ids = [i for i, f in flow.items() if f == name]
        by_flow[name] = dict(contrasts=len(ids), **{k: sum(kind[i] == k for i in ids) for k in order},
                             order_changes=sum(i in changes for i in ids), beyond_one_profile=sum(i in beyond for i in ids),
                             with_more_than_ten_resolved_comparisons=sum(resolved[i] > 10 for i in ids))
    result = dict(
        meaning="Post hoc description of the categories in contrast_outcomes_summary.json. No category, count or rule is changed. "
                "The kind of flow follows a keyword rule on the recorded case description and was assigned once.",
        contrasts=len(per),
        exclusive_outcome=dict((k, places[k]) for k in order),
        order_changes=len(changes), beyond_one_profile=len(beyond),
        beyond_one_profile_not_between_conditions=sorted(i for i in beyond if kind[i] != "between conditions"),
        by_resolved_comparisons=by_bin,
        one_order_with_five_or_fewer_resolved_comparisons=[sum(resolved[i] <= 5 for i in one_order), len(one_order)],
        resolved_comparisons_per_pair_by_theme=pairs,
        pairs_by_theme_exclusive=pairs_exclusive,
        crossing_points_and_wall_stress=crossing_and_stress,
        separating_factor_by_kind_of_flow={k: dict(sorted(v.items())) for k, v in factor_by_flow.items()},
        beyond_one_profile_by_theme=dict(sorted(themes_beyond.items())),
        flow_rule=[dict(kind=name, pattern=pattern) for name, pattern in FLOW_RULES],
        by_kind_of_flow=by_flow,
        beyond_one_profile_by_kind_of_flow={name: sorted(i for i in beyond if flow[i] == name) for name, _ in FLOW_RULES},
        per_contrast=[dict(contrast_id=d["contrast_id"], outcome=kind[d["contrast_id"]], resolved_comparisons=resolved[d["contrast_id"]],
                           kind_of_flow=flow[d["contrast_id"]]) for d in per])
    assert sum(result["exclusive_outcome"].values()) == len(per) == sum(b["contrasts"] for b in by_bin) + len(none)
    (ROOT / "results/revision/outcome_structure.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    print("exclusive", result["exclusive_outcome"], "beyond", len(beyond))
    for b in by_bin:
        print(b)
    print("one order with <=5 resolved", result["one_order_with_five_or_fewer_resolved_comparisons"])
    print({t: v["mean_per_pair"] for t, v in pairs.items()})
    for name, v in by_flow.items():
        print(name, v)


if __name__ == "__main__":
    main()
