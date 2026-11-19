"""Decide which printed directions of error change are resolved by the printed digits.

A printed number stands for the interval of values that round to it. A direction is resolved when the
sign of the change in absolute error is the same for every admissible combination of the alternative,
the baseline and the reference, including any reference interval the source reports. The rule text is
stored with the digit strings in data/revision/table_digits.json. Standard library only.
"""
import csv
import itertools
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/revision"
RESULTS = ROOT / "results/revision"


def box(text):
    """Interval of true values consistent with a printed string such as 0.2, 4.6 − 4.7 or 4.51 ± 0.06."""
    text = text.replace("−", "-")
    half = lambda s: 0.5 * 10 ** (-(len(s.split(".")[1]) if "." in s else 0))
    if "±" in text:
        value, spread = [s.strip() for s in text.split("±")]
        return float(value) - half(value) - float(spread), float(value) + half(value) + float(spread), float(value)
    parts = [s for s in re.split(r"\s+-\s+", text.strip()) if s]
    if len(parts) == 2:
        return float(parts[0]) - half(parts[0]), float(parts[1]) + half(parts[1]), 0.5 * (float(parts[0]) + float(parts[1]))
    return float(text) - half(text), float(text) + half(text), float(text)


def extremes(a, b, r):
    """Exact range of |a-r| - |b-r| over the three intervals. The function is piecewise linear."""
    candidates = {r[0], r[1]} | {v for v in (a[0], a[1], b[0], b[1]) if r[0] <= v <= r[1]}
    values = []
    for rv in candidates:
        ac = {a[0], a[1]} | ({rv} if a[0] <= rv <= a[1] else set())
        bc = {b[0], b[1]} | ({rv} if b[0] <= rv <= b[1] else set())
        values += [abs(x - rv) - abs(y - rv) for x, y in itertools.product(ac, bc)]
    return min(values), max(values)


def change(alternative, baseline, reference=None):
    a, b = box(alternative), box(baseline)
    r = (0.0, 0.0, 0.0) if reference is None else box(reference)
    low, high = extremes(a, b, r)
    direction = "closer" if high < 0 else "farther" if low > 0 else "unresolved"
    return dict(alternative=alternative, baseline=baseline, reference=reference,
                nominal_change=round(abs(a[2] - r[2]) - abs(b[2] - r[2]), 6),
                change_min=round(low, 6), change_max=round(high, 6), direction=direction)


def combine(by_reference):
    found = {v["direction"] for v in by_reference.values()}
    if found in ({"closer"}, {"farther"}):
        return found.pop()
    return "reference dependent" if {"closer", "farther"} <= found else "unresolved"


def classify(first, second, controls):
    if first not in ("closer", "farther") or second not in ("closer", "farther"):
        return "unresolved"
    if controls == "differ":
        return "controls differ"
    return "resolved concordant" if first == second else "resolved opposing"


def hill(row):
    out = dict(id=row["id"], study_id=row["study_id"], source_location=row["source_location"],
               controls_status=row["controls"]["status"])
    if row["baseline_printed"] is None or row["alternative_printed"] is None:
        return dict(out, **{"class": "unrankable"})
    crossings = {}
    for index, name in enumerate(("separation", "reattachment")):
        by_reference = {ref: change(row["alternative_printed"][index], row["baseline_printed"][index], printed[index])
                        for ref, printed in row["references"].items() if printed[index] is not None}
        crossings[name] = dict(direction=combine(by_reference), by_reference=by_reference)
    out.update(crossings)
    out["class"] = classify(crossings["separation"]["direction"], crossings["reattachment"]["direction"],
                            row["controls"]["status"])
    return out


def tally(rows):
    counts = {}
    for row in rows:
        counts[row["class"]] = counts.get(row["class"], 0) + 1
    return dict(sorted(counts.items()))


def bump_support():
    """Velocity ranking at x/L = -0.4 as a function of the wall-normal support."""
    with (DATA / "measurements/P31_Fig12c_DSM.csv").open(newline="") as stream:
        rows = sorted(({k: float(v) for k, v in r.items()} for r in csv.DictReader(stream)), key=lambda r: r["y_over_L"])
    y = [r["y_over_L"] for r in rows]
    eq = [r["EQWM_DSM_U_over_Uinf"] - r["PIV_U_over_Uinf"] for r in rows]
    rl = [r["RLWM_DSM_U_over_Uinf"] - r["PIV_U_over_Uinf"] for r in rows]
    mean = lambda v: sum(v) / len(v)
    mae = lambda v: mean([abs(x) for x in v])
    n = len(y)
    learned_closer_from = next(i for i in range(n - 4) if mae(eq[i:]) > mae(rl[i:]))
    assert all(mae(eq[i:]) > mae(rl[i:]) for i in range(learned_closer_from, n - 4))
    pointwise = next(i for i in range(n) if abs(eq[i]) > abs(rl[i]))
    assert all(abs(eq[i]) > abs(rl[i]) for i in range(pointwise, n))
    spacing, stretch = 9e-4, 1.013
    faces = [spacing * (stretch ** k - 1) / (stretch - 1) for k in range(80)]
    cell = lambda v: next(k for k in range(1, 80) if faces[k] >= v)
    part = lambda keep: dict(n=sum(keep), mean_signed_equilibrium=mean([e for e, k in zip(eq, keep) if k]),
                             mean_signed_learned=mean([e for e, k in zip(rl, keep) if k]),
                             mae_equilibrium=mae([e for e, k in zip(eq, keep) if k]),
                             mae_learned=mae([e for e, k in zip(rl, keep) if k]))
    cut = 0.5 * (y[pointwise - 1] + y[pointwise])
    above = part([v > 0.02 for v in y])
    return dict(
        source="arXiv:2305.02540v3, Fig. 12(c), x/L = -0.4, fine mesh, dynamic Smagorinsky closure",
        units="U/U_inf", full_support=dict(part([True] * n), y_min=y[0], y_max=y[-1]),
        ranking_by_full_support_mean_absolute_discrepancy="equilibrium closer",
        lower_bound_at_which_the_ranking_changes=[y[learned_closer_from - 1], y[learned_closer_from]],
        lower_bound_cell=cell(y[learned_closer_from]),
        pointwise_equal_error_between=[y[pointwise - 1], y[pointwise]],
        pointwise_cells=[cell(y[pointwise - 1]), cell(y[pointwise])],
        below_pointwise_crossover=part([v < cut for v in y]), above_pointwise_crossover=part([v > cut for v in y]),
        above_0p02=above, below_0p02=part([v <= 0.02 for v in y]),
        margin_above_0p02=above["mae_equilibrium"] - above["mae_learned"],
        reference_shift_that_would_reverse_the_ranking_above_0p02=0.5 * (above["mean_signed_equilibrium"] + above["mean_signed_learned"]),
        mesh=dict(min_dy_over_L=spacing, stretching=stretch, learned_wall_sample_height=faces[1],
                  equilibrium_matching_height=0.5 * (faces[1] + faces[2]), lowest_measured_height_cell=cell(y[0])),
        statistics="1.5 flow-through times after a 1.5 flow-through transient in each bump run (source p. 21). No sampling interval is reported.",
        experiment="Gray (2023), doctoral thesis: freestream velocity uncertainty about 0.4 % at 95 % confidence (Appendix G.1); "
                   "the PIV uncertainty treatment covers random error only (Section 2.4.5, Appendix G.4).")


def main():
    register = json.loads((DATA / "table_digits.json").read_text())
    population = [hill(r) for r in register["hill_population"]]
    sensitivity = [hill(r) for r in register["hill_same_table_sensitivity"]]
    tabulated = []
    for row in register["other_tabulated"]:
        outputs = {name: change(v["alternative"], v["baseline"]) for name, v in row["outputs"].items()}
        directions = [v["direction"] for v in outputs.values()]
        if len(directions) == 2:
            label = classify(directions[0], directions[1], "not differ")
        else:
            label = "unresolved" if directions[0] == "unresolved" else "resolved " + directions[0]
        tabulated.append(dict(id=row["id"], study_id=row["study_id"], outputs=outputs, **{"class": label}))
    ranked = [r for r in population if "separation" in r]
    first = lambda r, key: next(iter(r[key]["by_reference"].values()))["nominal_change"]
    opposite = [r for r in ranked if first(r, "separation") * first(r, "reattachment") <= 0]
    summary = dict(
        contrasts=len(population), works=len({r["study_id"] for r in population}), by_class=tally(population),
        ids_by_class={c: [r["id"] for r in population if r["class"] == c] for c in sorted({r["class"] for r in population})},
        resolved_with_documented_equal_controls={c: [r["id"] for r in population if r["class"] == c and r["controls_status"] == "documented equal"]
                                                 for c in ("resolved concordant", "resolved opposing")},
        nominal_point_signs=dict(both_closer=len(ranked) - len(opposite), opposite=len(opposite), unrankable=len(population) - len(ranked)),
        smaller_change_in_each_nominally_opposite_contrast={r["id"]: min(abs(first(r, "separation")), abs(first(r, "reattachment"))) for r in opposite},
        range_of_changes_in_resolved_concordant_contrasts=[
            min(abs(v["nominal_change"]) for r in population if r["class"] == "resolved concordant" for k in ("separation", "reattachment") for v in r[k]["by_reference"].values()),
            max(abs(v["nominal_change"]) for r in population if r["class"] == "resolved concordant" for k in ("separation", "reattachment") for v in r[k]["by_reference"].values())])
    result = dict(rule_sha256=register["rule_sha256"],
                  meaning="Resolved means resolved to the printed digits and reported reference intervals. Sampling, discretisation and "
                          "measurement uncertainty enter only where a source reports them.",
                  periodic_hill=dict(summary=summary, contrasts=population),
                  periodic_hill_same_table_sensitivity=dict(by_class=tally(sensitivity), contrasts=sensitivity),
                  other_tabulated=tabulated, bump_station_velocity=bump_support())
    (RESULTS / "direction_resolution.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("Hill contrasts by class:", summary["by_class"])


if __name__ == "__main__":
    main()
