"""Recompute the numbers of the three worked decisions from the stored readings and printed digits.

Inputs: data/revision/worked_decisions.json (cases, illustrative tolerances, reported uncertainty),
displayed_comparisons.json (step crossings), channel_scheme_table.json (printed strings of the channel tables),
results/revision/direction_resolution.json (bump station profile). Output: results/revision/worked_decisions.json.
A tolerance decision follows the manuscript rule: an interval for the signed discrepancy inside [-T, T] supports
agreement, a disjoint interval supports a miss, partial overlap leaves the decision open. The only intervals available
here are reading or printing precision; they are not physical uncertainty. Standard library only.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve_directions import box, change

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/revision"
RESULTS = ROOT / "results/revision"


def verdict(low, high, tolerance):
    if -tolerance <= low and high <= tolerance:
        return "inside"
    if low > tolerance or high < -tolerance:
        return "outside"
    return "open"


def step(case):
    read = json.loads((DATA / "displayed_comparisons.json").read_text())["readings"]["Dupuy2023"]["digitised"]
    q = {k: round(read[name]["zero_crossing_x_over_h"], 1) for k, name in (("baseline", "wall law"), ("model", "GNN N=4"), ("reference", "WR reference"))}
    half = case["reading_precision"]          # each crossing is quoted to the nearest tenth; a discrepancy of two readings to 0.1
    out = dict(crossings=q, tolerance=case["illustrative_tolerance"])
    for name in ("baseline", "model"):
        d = round(q[name] - q["reference"], 1)
        out[name] = dict(signed_discrepancy=d, interval_at_reading_precision=[round(d - half, 1), round(d + half, 1)],
                         against_tolerance=verdict(d - half, d + half, case["illustrative_tolerance"]))
    out["gain_in_absolute_error"] = round(abs(out["baseline"]["signed_discrepancy"]) - abs(out["model"]["signed_discrepancy"]), 1)
    out["shortfall_beyond_tolerance"] = round(abs(out["model"]["signed_discrepancy"]) - case["illustrative_tolerance"], 1)
    out["reference_shift_that_would_bring_the_model_within_tolerance"] = round(-out["shortfall_beyond_tolerance"], 1)
    return out


def channel(case):
    table = json.loads((DATA / "channel_scheme_table.json").read_text())
    tol = case["illustrative_tolerance"]
    rows, out = [], dict(tolerance=tol)
    for t in table["tables"]:
        none, wall = t["printed"]["no_wall_model"], t["printed"]["spalding"]
        for scheme, (i_u, i_o) in (("linear", (0, 2)), ("LUST", (1, 3))):
            friction = change(wall[i_u], none[i_u])
            outer = change(wall[i_o], none[i_o])
            u = box(wall[i_u]); o = box(wall[i_o])
            rows.append(dict(closure=t["closure"], scheme=scheme,
                             friction_error_percent=dict(without=none[i_u], with_wall_law=wall[i_u], direction=friction["direction"],
                                                         against_tolerance=verdict(u[0], u[1], tol["friction_velocity_percent"])),
                             outer_error_percent=dict(without=none[i_o], with_wall_law=wall[i_o], direction=outer["direction"],
                                                      change=round(float(wall[i_o]) - float(none[i_o]), 2),
                                                      against_tolerance=verdict(o[0], o[1], tol["outer_velocity_percent"]))))
    out["pairs"] = rows
    for scheme in ("linear", "LUST"):
        mine = [r for r in rows if r["scheme"] == scheme]
        fr = [abs(float(r["friction_error_percent"]["with_wall_law"])) for r in mine]
        ou = [float(r["outer_error_percent"]["with_wall_law"]) for r in mine]
        out[scheme] = dict(
            friction_closer=sum(r["friction_error_percent"]["direction"] == "closer" for r in mine),
            outer_closer=sum(r["outer_error_percent"]["direction"] == "closer" for r in mine),
            outer_farther=sum(r["outer_error_percent"]["direction"] == "farther" for r in mine),
            friction_error_range_with_wall_law=[min(fr), max(fr)], outer_error_range_with_wall_law=[min(ou), max(ou)],
            outer_change_range=[min(r["outer_error_percent"]["change"] for r in mine), max(r["outer_error_percent"]["change"] for r in mine)],
            friction_inside_tolerance=sum(r["friction_error_percent"]["against_tolerance"] == "inside" for r in mine),
            outer_inside_tolerance=sum(r["outer_error_percent"]["against_tolerance"] == "inside" for r in mine),
            outer_outside_tolerance=sum(r["outer_error_percent"]["against_tolerance"] == "outside" for r in mine))
    out["smallest_outer_change"] = min((abs(r["outer_error_percent"]["change"]), r["closure"], r["scheme"]) for r in rows)
    return out


def bump(case):
    station = json.loads((RESULTS / "direction_resolution.json").read_text())["bump_station_velocity"]
    f, tol = case["friction_times_1000"], case["illustrative_tolerance"]
    out = dict(tolerance=tol)
    for name in ("equilibrium", "learned"):
        d = f[name] - f["experiment_interpolated"]
        low, high = d - f["reading_precision"], d + f["reading_precision"]
        pct = lambda v: 100 * v / f["experiment_interpolated"]
        out[f"friction_{name}"] = dict(signed_discrepancy_times_1000=round(d, 2), percent=round(pct(d), 2),
                                       percent_interval_at_reading_precision=[round(pct(low), 2), round(pct(high), 2)],
                                       against_tolerance=verdict(pct(low), pct(high), tol["friction_percent"]))
    full, above = station["full_support"], station["above_0p02"]
    p = case["velocity_reading_precision"]
    for name, key in (("equilibrium", "mae_equilibrium"), ("learned", "mae_learned")):
        v = full[key]
        out[f"velocity_{name}"] = dict(mean_absolute_discrepancy=round(v, 6), above_0p02=round(above[key], 6),
                                       against_tolerance="inside" if v + p <= tol["velocity_mean_absolute_in_freestream_units"] else
                                       "outside" if v - p > tol["velocity_mean_absolute_in_freestream_units"] else "open")
    out["closer_on_friction"] = "learned" if abs(out["friction_learned"]["percent"]) < abs(out["friction_equilibrium"]["percent"]) else "equilibrium"
    out["closer_on_velocity_full_support"] = "learned" if full["mae_learned"] < full["mae_equilibrium"] else "equilibrium"
    out["closer_on_velocity_above_0p02"] = "learned" if above["mae_learned"] < above["mae_equilibrium"] else "equilibrium"
    out["velocity_margin_full_support"] = round(full["mae_learned"] - full["mae_equilibrium"], 6)
    out["velocity_margin_above_0p02"] = round(station["margin_above_0p02"], 6)
    out["freestream_uncertainty_in_freestream_units"] = case["uncertainty_reported"]["freestream_velocity_percent_95"] / 100
    out["friction_bias_percent"] = case["uncertainty_reported"]["friction_bias_percent"]
    return out


def design_size(p_ordinary=0.30, p_questions=0.10, z_alpha=1.959964, z_power=0.841621):
    """Independent decisions per arm for a two-sided 5 % test of two proportions at 80 % power (normal approximation,
    pooled variance under the null). An illustration for the proposed comparison: no such study has been run."""
    mean = (p_ordinary + p_questions) / 2
    a = z_alpha * (2 * mean * (1 - mean)) ** 0.5
    b = z_power * (p_ordinary * (1 - p_ordinary) + p_questions * (1 - p_questions)) ** 0.5
    n = (a + b) ** 2 / (p_ordinary - p_questions) ** 2
    return dict(false_acceptance_ordinary=p_ordinary, false_acceptance_with_questions=p_questions, two_sided_alpha=0.05, power=0.80,
                decisions_per_arm=round(n, 1), assumption="independent decisions; clustering by shared model or benchmark raises the number",
                status="design only; no observation")


def main():
    cases = {c["id"]: c for c in json.loads((DATA / "worked_decisions.json").read_text())["cases"]}
    result = dict(meaning="Tolerances are illustrative. Intervals are reading or printing precision only; no case has a published interval "
                          "for sampling, discretisation and reference uncertainty together.",
                  step=step(cases["step"]), channel=channel(cases["channel"]), bump=bump(cases["bump"]),
                  prospective_design=design_size())
    (RESULTS / "worked_decisions.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    s, c, b = result["step"], result["channel"], result["bump"]
    print("step", s["baseline"]["signed_discrepancy"], s["model"]["signed_discrepancy"], s["model"]["against_tolerance"])
    print("channel linear", c["linear"]); print("channel LUST", c["LUST"])
    print("design", result["prospective_design"]["decisions_per_arm"])
    print("bump", {k: v for k, v in b.items() if k.startswith(("friction_", "velocity_", "closer"))})


if __name__ == "__main__":
    main()
