"""Derive the outcome categories of the matched wall-treatment contrasts from the recorded rows.

Input: data/revision/contrast_outcomes.json (one record per member contrast: roles of the arms, a theme for each pair
of arm 0 with another arm, and one row per quantity, set of conditions and source location), the Level-2 contrast
records (bases), data/revision/study_families.json and, for the works read twice, data/revision/outcome_agreement.json.
The rule text is stored in the data file. No category is typed by a reader: this script applies Section 5 of the rule.
A tabulated row carries the printed strings; its direction is decided here by the digit-interval rule of
resolve_directions.py. Output: results/revision/contrast_outcomes_summary.json. Needs numpy (python3 -I).
"""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve_directions import box, change, combine

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/revision"
RESULTS = ROOT / "results/revision"
CLASSES = ("wall_stress", "separation", "mean_velocity", "pressure", "turbulence", "load", "heat", "other")
THEMES = ("balance", "inputs", "location", "imposition", "law", "learned", "parameter", "on_off", "resolution", "other")
ROLES = ("baseline", "proposed", "neither")
NAMED = ("first", "other")                     # the row names arm 0 or arm j as the closer arm
RESOLVED = ("first", "other", "region")
BASES = ("collection", "without_boundary_cases", "primary_scope")
CATEGORIES = ("one order", "order changes", "nothing resolved")


MISSING = ("", "-", "--", "n/a", "na", "none", "null", "not given", "not reported")


def absent(value):
    """A cell that the source leaves empty or fills with a dash of any length."""
    return re.sub(r"[\u2010-\u2015\u2212]", "-", str(value).strip().lower()) in MISSING


def clean(text):
    """A printed number as copied by a reader: unit signs and a leading plus are dropped, digits are kept as printed.
    A printed range (4.6 - 4.7) or spread (6.0 ± 0.15) is kept for the interval rule."""
    text = str(text).strip().replace("\u2212", "-").replace("\u2013", "-").replace("%", "").replace(",", "")
    text = re.sub(r"\s*(x|\u00d7)\s*10\^?\{?(-?\d+)\}?$", "", text)   # a common factor in a table header does not change the order
    text = re.sub(r"\s*(\+/-|\+-)\s*", " \u00b1 ", text)
    text = text.lstrip("+").strip()
    box(text)                                     # raises ValueError for anything the interval rule cannot read
    return text


def printed_direction(entry, j):
    """Direction of pair (0, j) from printed strings: 'first', 'other', 'unresolved' or 'reference-dependent'."""
    arms = entry.get("arms") or {}
    if any(absent(arms.get(k, "")) for k in ("0", str(j))):
        return "not_comparable", None
    try:
        a0, aj = clean(arms["0"]), clean(arms[str(j)])
        kind = entry.get("printed_as", "value")
        if kind == "value":
            refs = [clean(r) for r in entry.get("reference") or [] if not absent(r)]
            if not refs:
                return "not_comparable", None
            by_ref = {r: change(aj, a0, r) for r in refs}
        else:
            by_ref = {"error": change(aj, a0, None)}
    except (ValueError, IndexError):
        return "not_comparable", "printed string is not a number"
    found = combine(by_ref)
    return {"closer": "other", "farther": "first", "unresolved": "unresolved", "reference dependent": "reference-dependent"}[found], by_ref


def cells(record):
    """One cell per pair, row and condition: (j, class, condition, direction, row_id, kind)."""
    n = record["n_arms"]
    known = [c["id"] for c in record.get("conditions") or []] or ["c1"]
    out = []
    for row in record["rows"]:
        assert row["class"] in CLASSES, (record["contrast_id"], row.get("row_id"), row["class"])
        if row["kind"] == "tabulated":
            for entry in row.get("printed") or []:
                for j in range(1, n):
                    direction, detail = printed_direction(entry, j)
                    out.append(dict(j=j, cls=row["class"], condition=str(entry.get("condition") or known[0]), direction=direction,
                                    row_id=row["row_id"], kind="tabulated"))
            continue
        conditions = [str(c) for c in (row.get("conditions") or known)]
        for key, value in (row.get("directions") or {}).items():
            j = int(key)
            assert 1 <= j < n, (record["contrast_id"], row["row_id"], key)
            closer = value.get("closer_arm")
            closer = str(closer).strip().lower()
            direction = ("first" if closer == "0" else "other" if closer == str(j) else closer if closer in ("region", "unresolved") else
                         "not_comparable")
            for c in conditions:
                out.append(dict(j=j, cls=row["class"], condition=c, direction=direction, row_id=row["row_id"], kind="plotted"))
    return out


def pair_category(cs):
    """Section 5 and clarification O1, over the hydrodynamic cells of one pair."""
    found = {c["direction"] for c in cs}
    named = found & set(NAMED)
    if len(named) == 2 or "region" in found:
        return "order changes"
    if named:
        return "one order"
    return "reference-dependent only" if "reference-dependent" in found else "nothing resolved"


def where_changes(cs):
    """Where the order of one pair changes; the labels are not exclusive."""
    labels = set()
    named = [c for c in cs if c["direction"] in NAMED]
    if any(c["direction"] == "region" for c in cs):
        labels.add("within a profile")
    for a in named:
        for b in named:
            if a["direction"] == b["direction"]:
                continue
            if a["cls"] != b["cls"] and a["condition"] == b["condition"]:
                labels.add("between quantities")
            if a["cls"] == b["cls"] and a["condition"] != b["condition"]:
                labels.add("between conditions")
            if a["cls"] == b["cls"] and a["condition"] == b["condition"]:
                labels.add("within a class")
    return labels


def shared_classes(cs):
    """Classes with a resolved cell under a condition that carries resolved cells of two or more classes."""
    by_condition = {}
    for c in cs:
        if c["direction"] in RESOLVED:
            by_condition.setdefault(c["condition"], set()).add(c["cls"])
    return [sorted(v) for v in by_condition.values() if len(v) >= 2]


def class_pairs_that_differ(cs):
    named = [c for c in cs if c["direction"] in NAMED]
    return sorted({tuple(sorted((a["cls"], b["cls"]))) for a in named for b in named
                   if a["cls"] != b["cls"] and a["condition"] == b["condition"] and a["direction"] != b["direction"]})


def class_pairs_compared(cs):
    """Pairs of classes that both carry a named direction under one condition."""
    named = [c for c in cs if c["direction"] in NAMED]
    return sorted({tuple(sorted((a["cls"], b["cls"]))) for a in named for b in named if a["cls"] != b["cls"] and a["condition"] == b["condition"]})


def conditions_that_differ(cs):
    """(class, condition, condition) for named cells of one class that give opposite orders under two conditions."""
    named = [c for c in cs if c["direction"] in NAMED]
    return sorted({(a["cls"],) + tuple(sorted((a["condition"], b["condition"]))) for a in named for b in named
                   if a["cls"] == b["cls"] and a["condition"] != b["condition"] and a["direction"] != b["direction"]})


def derive(record):
    """Categories of one contrast. Heat rows are kept out of every hydrodynamic category."""
    n = record["n_arms"]
    assert len(record["arm_roles"]) == n and all(r in ROLES for r in record["arm_roles"]), record["contrast_id"]
    themes = {p["arm"]: p["theme"] for p in record["pairs"]}
    assert sorted(themes) == list(range(1, n)) and all(t in THEMES for t in themes.values()), record["contrast_id"]
    every = cells(record)
    hydro = [c for c in every if c["cls"] != "heat"]
    pairs = []
    for j in range(1, n):
        mine = [c for c in hydro if c["j"] == j]
        usable = [c for c in mine if c["direction"] != "not_comparable"]
        category = pair_category(usable)
        roles = (record["arm_roles"][0], record["arm_roles"][j])
        alternative = j if roles[0] == "baseline" and roles[1] != "baseline" else 0 if roles[1] == "baseline" and roles[0] != "baseline" else None
        oriented = None
        if alternative is not None:
            want = "other" if alternative == j else "first"
            named = {c["direction"] for c in usable} & set(NAMED)
            oriented = ("order changes" if category == "order changes" else
                        "alternative closer" if named == {want} else "baseline closer" if named else "nothing resolved")
        by_class = {}
        for cls in CLASSES:
            got = {c["direction"] for c in usable if c["cls"] == cls}
            if got:
                named = got & set(NAMED)
                by_class[cls] = ("changes" if len(named) == 2 or "region" in got else named.pop() if named else "unresolved")
        pairs.append(dict(arm=j, theme=themes[j], category=category, where=sorted(where_changes(usable)) if category == "order changes" else [],
                          every_cell_resolved=bool(usable) and all(c["direction"] in RESOLVED for c in usable),
                          has_unresolved=any(c["direction"] in ("unresolved", "reference-dependent") for c in usable),
                          shared_classes=shared_classes(usable), classes_that_differ=[list(p) for p in class_pairs_that_differ(usable)],
                          classes_compared=[list(p) for p in class_pairs_compared(usable)],
                          conditions_that_differ=[list(p) for p in conditions_that_differ(usable)],
                          alternative_arm=alternative, oriented=oriented, direction_by_class=by_class,
                          cells=len(usable), cells_unresolved=sum(c["direction"] in ("unresolved", "reference-dependent") for c in usable)))
    found = [p["category"] for p in pairs]
    category = "order changes" if "order changes" in found else "one order" if "one order" in found else "nothing resolved"
    where = sorted({w for p in pairs for w in p["where"]})
    defined = any(p["shared_classes"] for p in pairs)
    return dict(contrast_id=record["contrast_id"], study_id=record["study_id"], category=category, where=where,
                every_cell_resolved=all(p["every_cell_resolved"] for p in pairs),
                two_classes_under_a_shared_condition=defined, changes_between_quantities="between quantities" in where,
                classes_that_differ=sorted({tuple(x) for p in pairs for x in p["classes_that_differ"]}),
                classes_compared=sorted({tuple(x) for p in pairs for x in p["classes_compared"]}),
                conditions_that_differ=sorted({tuple(x) for p in pairs for x in p["conditions_that_differ"]}),
                themes=sorted({p["theme"] for p in pairs}), pairs=pairs,
                rows=len(record["rows"]), heat_rows=sum(r["class"] == "heat" for r in record["rows"]),
                plotted_rows=sum(r["kind"] == "plotted" for r in record["rows"]), tabulated_rows=sum(r["kind"] == "tabulated" for r in record["rows"]))


def tally(derived):
    """E1 and E2 over a set of derived contrasts, with the bounds of Section 5."""
    n = len(derived)
    e1 = Counter(d["category"] for d in derived)
    firm_one = sum(d["category"] == "one order" and d["every_cell_resolved"] for d in derived)
    could_change = sum(d["category"] != "order changes" and not (d["category"] == "one order" and d["every_cell_resolved"]) for d in derived)
    defined = [d for d in derived if d["two_classes_under_a_shared_condition"]]
    e2 = sum(d["changes_between_quantities"] for d in defined)
    where = Counter(w for d in derived for w in d["where"])
    return dict(contrasts=n, e1={k: e1.get(k, 0) for k in CATEGORIES},
                e1_bounds=dict(one_order=[firm_one, e1.get("one order", 0) + e1.get("nothing resolved", 0)],
                               order_changes=[e1.get("order changes", 0), e1.get("order changes", 0) + could_change]),
                where_the_order_changes={k: where.get(k, 0) for k in ("between quantities", "between conditions", "within a profile", "within a class")},
                e2=dict(contrasts_with_two_classes_under_a_shared_condition=len(defined), order_differs_between_quantities=e2,
                        ids=sorted(d["contrast_id"] for d in defined if d["changes_between_quantities"]),
                        class_pairs={k: dict(compared=n, differ=sum(tuple(k.split(" / ")) in d["classes_that_differ"] for d in derived))
                                     for k, n in sorted(Counter(" / ".join(p) for d in derived for p in d["classes_compared"]).items())}))


def roll_up(derived, key):
    """A work or family is 'order changes' if any of its contrasts is, else 'one order' if any is."""
    groups = {}
    for d in derived:
        groups.setdefault(key(d), []).append(d["category"])
    out = Counter("order changes" if "order changes" in v else "one order" if "one order" in v else "nothing resolved" for v in groups.values())
    return dict(units=len(groups), **{k: out.get(k, 0) for k in CATEGORIES})


def oriented_classes(pairs):
    """For pairs with one baseline arm: per quantity class, whether the alternative or the baseline lies closer."""
    out = {}
    for p in pairs:
        if p["alternative_arm"] is None:
            continue
        want = "other" if p["alternative_arm"] == p["arm"] else "first"
        for cls, direction in p["direction_by_class"].items():
            label = direction if direction in ("changes", "unresolved") else "alternative closer" if direction == want else "baseline closer"
            out.setdefault(cls, Counter())[label] += 1
    return {c: dict(sorted(v.items())) for c, v in sorted(out.items())}


def kappa_multi(a, b):
    a, b = np.asarray(a), np.asarray(b)
    labels = sorted(set(a) | set(b))
    po = float(np.mean(a == b))
    pe = float(sum(np.mean(a == k) * np.mean(b == k) for k in labels))
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def agreement(units, rng, resamples=10000):
    """units: list of (work, first label, second label). Percentile bootstrap over works."""
    if not units:
        return dict(n=0, agree=0, kappa=None, kappa_bootstrap_95=None)
    works = sorted({u[0] for u in units})
    by_work = {w: [(a, b) for x, a, b in units if x == w] for w in works}
    a, b = [u[1] for u in units], [u[2] for u in units]
    values = []
    for _ in range(resamples):
        draw = [p for w in rng.choice(works, len(works)) for p in by_work[w]]
        k = kappa_multi([p[0] for p in draw], [p[1] for p in draw])
        if k == k:
            values.append(k)
    k = kappa_multi(a, b)
    return dict(n=len(units), works=len(works), agree=int(sum(x == y for x, y in zip(a, b))), kappa=None if k != k else round(k, 4),
                kappa_bootstrap_95=[round(float(np.percentile(values, 2.5)), 4), round(float(np.percentile(values, 97.5)), 4)] if values else None,
                table=dict(sorted(Counter(f"{x} | {y}" for x, y in zip(a, b)).items())))


def compare(first, second, seed):
    """Labels S1 to S5 of the plan for the works read twice. `first` and `second` map contrast id to (record, derived)."""
    rng = np.random.default_rng(seed)
    ids = sorted(set(first) & set(second))
    s1 = [(first[i][1]["study_id"], first[i][1]["category"], second[i][1]["category"]) for i in ids]
    s2, only_first, only_second = [], 0, 0
    s4, s5 = [], []
    for i in ids:
        (ra, da), (rb, db) = first[i], second[i]
        for pa, pb in zip(da["pairs"], db["pairs"]):
            assert pa["arm"] == pb["arm"]
            for cls in CLASSES:
                if cls == "heat":
                    continue
                x, y = pa["direction_by_class"].get(cls), pb["direction_by_class"].get(cls)
                if x and y:
                    s2.append((da["study_id"], x, y))
                elif x:
                    only_first += 1
                elif y:
                    only_second += 1
            s4.append((da["study_id"], pa["theme"], pb["theme"]))
        for x, y in zip(ra["arm_roles"], rb["arm_roles"]):
            s5.append((da["study_id"], x == "baseline", y == "baseline"))
    both_defined = [i for i in ids if first[i][1]["two_classes_under_a_shared_condition"] and second[i][1]["two_classes_under_a_shared_condition"]]
    s3 = [(first[i][1]["study_id"], first[i][1]["changes_between_quantities"], second[i][1]["changes_between_quantities"]) for i in both_defined]
    out = dict(contrasts=len(ids), works=len({first[i][1]["study_id"] for i in ids}),
               S1_contrast_category=agreement(s1, rng), S2_direction_by_pair_and_class=agreement(s2, rng),
               S2_coverage=dict(cells_in_both=len(s2), only_first=only_first, only_second=only_second),
               S3_change_between_quantities=agreement(s3, rng), S4_theme=agreement(s4, rng), S5_baseline_role=agreement(s5, rng))
    out["S1_contrast_category"]["order_changes_first"] = sum(u[1] == "order changes" for u in s1)
    out["S1_contrast_category"]["order_changes_second"] = sum(u[2] == "order changes" for u in s1)
    out["S3_change_between_quantities"]["defined_in_first_only"] = sum(first[i][1]["two_classes_under_a_shared_condition"] and not second[i][1]["two_classes_under_a_shared_condition"] for i in ids)
    out["S3_change_between_quantities"]["defined_in_second_only"] = sum(second[i][1]["two_classes_under_a_shared_condition"] and not first[i][1]["two_classes_under_a_shared_condition"] for i in ids)
    out["S3_change_between_quantities"]["yes_first"] = sum(first[i][1]["changes_between_quantities"] for i in ids)
    out["S3_change_between_quantities"]["yes_second"] = sum(second[i][1]["changes_between_quantities"] for i in ids)
    out["differing_contrasts"] = sorted(i for i in ids if first[i][1]["category"] != second[i][1]["category"] or any(
        pa["direction_by_class"].get(c) != pb["direction_by_class"].get(c) for pa, pb in zip(first[i][1]["pairs"], second[i][1]["pairs"])
        for c in CLASSES if c != "heat" and pa["direction_by_class"].get(c) and pb["direction_by_class"].get(c)))
    return out


def reproduced(stat, margin=None):
    """Thresholds of the plan: kappa >= 0.60, lower bound >= 0.40, and for S1 a member count within max(1, 15 %)."""
    if stat.get("kappa") is None or stat.get("kappa_bootstrap_95") is None:
        return False
    ok = stat["kappa"] >= 0.60 and stat["kappa_bootstrap_95"][0] >= 0.40
    if margin is not None:
        a, b = margin
        ok = ok and abs(a - b) <= max(1, 0.15 * max(a, b))
    return bool(ok)


def families(works):
    """Connected groups of the member works under the recorded links; an unlinked work is its own group."""
    links = json.loads((DATA / "study_families.json").read_text())["links"]
    parent = {w: w for w in works}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for link in links:
        inside = [w for w in link["works"] if w in parent]
        for w in inside[1:]:
            parent[find(w)] = find(inside[0])
    return {w: find(w) for w in works}


def main():
    data = json.loads((DATA / "contrast_outcomes.json").read_text())
    assert hashlib.sha256(data["rule"]["text"].encode()).hexdigest() == data["rule"]["sha256_of_rule_file"]
    level2 = {c["contrast_id"]: c for c in json.loads((DATA / "wall_change_contrasts.json").read_text())["records"]}
    works = json.loads((DATA / "source_dispositions.json").read_text())["records"]
    boundary = {w["study_id"] for w in works if w.get("scope_boundary")}
    members = sorted(i for i, c in level2.items() if c["work_counted"] and c["derived"]["tier"] in ("strict", "broad"))
    records = {r["contrast_id"]: r for r in data["records"]}
    assert sorted(records) == members, (set(members) ^ set(records))
    derived = {}
    for i in members:
        assert records[i]["n_arms"] == len(level2[i]["arms"]) and records[i]["study_id"] == level2[i]["study_id"], i
        derived[i] = derive(records[i])
    additions = json.loads((DATA / "level3_additions.json").read_text())
    moved_out = {c["contrast_id"] for c in additions["regime_corrections"] if c["corrected"]["primary_scope"] == "outside"}
    assert all(level2[i]["regime"]["primary_scope"] == "inside" for i in moved_out)
    basis = dict(collection=members,
                 without_boundary_cases=[i for i in members if level2[i]["study_id"] not in boundary and level2[i].get("sublayer_class") != "S"],
                 primary_scope=[i for i in members if level2[i]["regime"]["primary_scope"] == "inside" and i not in moved_out])
    family = families(sorted({level2[i]["study_id"] for i in members}))
    summary = {}
    for name, ids in basis.items():
        mine = [derived[i] for i in ids]
        summary[name] = dict(tally(mine), works=roll_up(mine, lambda d: d["study_id"]), families=roll_up(mine, lambda d: family[d["study_id"]]))
        pairs = [(d, p) for d in mine for p in d["pairs"]]
        summary[name]["pairs"] = dict(
            n=len(pairs), by_category=dict(sorted(Counter(p["category"] for _, p in pairs).items())),
            oriented=dict(n=sum(p["oriented"] is not None for _, p in pairs),
                          alternative_is_the_proposal_of_the_source=sum(
                              records[d["contrast_id"]]["arm_roles"][p["alternative_arm"]] == "proposed" for d, p in pairs if p["alternative_arm"] is not None),
                          by_category=dict(sorted(Counter(p["oriented"] for _, p in pairs if p["oriented"]).items()))),
            cells=sum(p["cells"] for _, p in pairs), cells_unresolved=sum(p["cells_unresolved"] for _, p in pairs))
        summary[name]["bounds_only"] = 2 * summary[name]["pairs"]["cells_unresolved"] > summary[name]["pairs"]["cells"]
        summary[name]["by_theme"] = {
            t: dict(pairs=sum(p["theme"] == t for _, p in pairs),
                    by_category=dict(sorted(Counter(p["category"] for _, p in pairs if p["theme"] == t).items())),
                    oriented=dict(sorted(Counter(p["oriented"] for _, p in pairs if p["theme"] == t and p["oriented"]).items())),
                    contrasts=len({d["contrast_id"] for d, p in pairs if p["theme"] == t}),
                    contrasts_order_changes=len({d["contrast_id"] for d, p in pairs if p["theme"] == t and p["category"] == "order changes"}),
                    works=len({d["study_id"] for d, p in pairs if p["theme"] == t}),
                    works_order_changes=len({d["study_id"] for d, p in pairs if p["theme"] == t and p["category"] == "order changes"}),
                    families=len({family[d["study_id"]] for d, p in pairs if p["theme"] == t}),
                    families_order_changes=len({family[d["study_id"]] for d, p in pairs if p["theme"] == t and p["category"] == "order changes"}),
                    oriented_by_class=oriented_classes([p for _, p in pairs if p["theme"] == t]))
            for t in THEMES if any(p["theme"] == t for _, p in pairs)}
        by_class = {}
        for _, p in pairs:
            for cls, direction in p["direction_by_class"].items():
                by_class.setdefault(cls, Counter())[direction] += 1
        summary[name]["direction_by_class_pairs"] = {c: dict(sorted(v.items())) for c, v in sorted(by_class.items())}
        summary[name]["oriented_direction_by_class_pairs"] = oriented_classes([p for _, p in pairs])
    coded = additions["condition_factors"]["contrasts"]
    between = sorted(i for i in members if "between conditions" in derived[i]["where"])
    assert sorted(coded) == between, (set(coded) ^ set(between))
    for i, entries in coded.items():
        found = {tuple(x[1:]) for x in derived[i]["conditions_that_differ"]}
        known = {c["id"] for c in records[i]["conditions"]}
        assert all(tuple(e["conditions"]) in found and set(e["conditions"]) <= known and e["factor"] in additions["condition_factors"]["values"]
                   for e in entries), i
        assert len(entries) == 1 or all(e["factor"] != "several together" for e in entries), i
    for name, ids in basis.items():
        mine = [i for i in ids if i in coded]
        by_factor = Counter(f for i in mine for f in {e["factor"] for e in coded[i]})
        summary[name]["between_conditions_by_factor"] = dict(
            contrasts=len(mine), works=len({level2[i]["study_id"] for i in mine}),
            by_factor={f: dict(contrasts=by_factor.get(f, 0), works=len({level2[i]["study_id"] for i in mine if any(e["factor"] == f for e in coded[i])}))
                       for f in additions["condition_factors"]["values"]},
            coding="coded once; see data/revision/level3_additions.json")
        e2_ids = summary[name]["e2"]["ids"]
        summary[name]["e2"]["works"] = len({level2[i]["study_id"] for i in e2_ids})
        summary[name]["e2"]["families"] = len({family[level2[i]["study_id"]] for i in e2_ids})
        changed = [d for d in (derived[i] for i in ids) if d["category"] == "order changes"]
        summary[name]["order_changes_only_within_a_profile"] = sum(d["where"] == ["within a profile"] for d in changed)
        summary[name]["order_changes_beyond_a_profile"] = sum(d["where"] != ["within a profile"] for d in changed)
        summary[name]["pairs"]["share_of_cells_unresolved_percent"] = round(100 * summary[name]["pairs"]["cells_unresolved"] / summary[name]["pairs"]["cells"])
    out = dict(rule_sha256=data["rule"]["sha256_of_rule_file"],
               meaning="Counts describe the member contrasts of a retrieved collection. Resolved means resolved to the printed digits or to the "
                       "stroke width of the plotted curves. No count estimates a frequency for the literature.",
               population=dict(contrasts=len(members), works=len({level2[i]["study_id"] for i in members}),
                               pairs=sum(len(derived[i]["pairs"]) for i in members),
                               rows=sum(d["rows"] for d in derived.values()), heat_rows=sum(d["heat_rows"] for d in derived.values()),
                               plotted_rows=sum(d["plotted_rows"] for d in derived.values()), tabulated_rows=sum(d["tabulated_rows"] for d in derived.values()),
                               families=len(set(family.values())), basis_sizes={k: len(v) for k, v in basis.items()},
                               works_by_edition_read=dict(sorted(Counter({records[i]["study_id"]: records[i]["edition_read"]["kind"]
                                                                          for i in members}.values()).items())),
                               contrasts_by_reading=dict(sorted(Counter(records[i]["reading"].split(" (")[0] for i in members).items()))),
               summary=summary, per_contrast=[derived[i] for i in members])
    agreement_file = DATA / "outcome_agreement.json"
    if agreement_file.exists():
        twice = json.loads(agreement_file.read_text())
        first = {r["contrast_id"]: (r, derive(r)) for r in twice["first_reading"]}
        second = {r["contrast_id"]: (r, derive(r)) for r in twice["second_reading"]}
        stats = compare(first, second, twice["bootstrap_seed"])
        s1 = stats["S1_contrast_category"]
        decisions = dict(
            E1_quotable=reproduced(s1, (s1["order_changes_first"], s1["order_changes_second"])),
            E2_quotable=reproduced(stats["S3_change_between_quantities"]) or (
                max(stats["S3_change_between_quantities"]["yes_first"], stats["S3_change_between_quantities"]["yes_second"]) < 5
                and stats["S3_change_between_quantities"]["agree"] == stats["S3_change_between_quantities"]["n"]),
            themes_quotable=reproduced(stats["S4_theme"]), oriented_quotable=reproduced(stats["S5_baseline_role"]),
            by_class_quotable=reproduced(stats["S2_direction_by_pair_and_class"]))
        check = twice.get("regime_check")
        if check:
            rng = np.random.default_rng(twice["bootstrap_seed"])
            rows = check["rows"]
            assert {r["contrast_id"] for r in rows} == set(first)
            for key in ("primary_scope", "sublayer_class"):
                assert all(r["level2"][key] == (level2[r["contrast_id"]]["regime"][key] if key == "primary_scope" else level2[r["contrast_id"]][key]) for r in rows)
            scope = [r["contrast_id"] for r in rows if r["level2"]["primary_scope"] != r["check"]["primary_scope"]]
            cell = {r["contrast_id"]: [r["level2"]["sublayer_class"], r["check"]["sublayer_class"]] for r in rows
                    if r["level2"]["sublayer_class"] != r["check"]["sublayer_class"]}
            would_leave = sorted(i for i, (was, now) in cell.items() if now == "S" and i in basis["without_boundary_cases"])
            stats["S6_primary_scope"] = agreement([(r["study_id"], r["level2"]["primary_scope"], r["check"]["primary_scope"]) for r in rows], rng)
            stats["S6_first_cell_class"] = agreement([(r["study_id"], r["level2"]["sublayer_class"], r["check"]["sublayer_class"]) for r in rows], rng)
            stats["S6_differing"] = dict(primary_scope=scope, first_cell_class=cell, would_leave_the_basis_without_boundary_cases=would_leave)
            decisions["primary_scope_basis_read_once"] = bool(scope)
        out["agreement"] = dict(sample=twice["sample"], statistics=stats, decisions=decisions,
                                thresholds="kappa >= 0.60, lower 95 % bootstrap bound >= 0.40; for S1 the numbers of 'order changes' "
                                           "contrasts differ by at most max(1, 15 %)")
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "contrast_outcomes_summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    s = summary["collection"]
    print("contrasts", s["contrasts"], "| E1", s["e1"], "| bounds", s["e1_bounds"], "| E2", s["e2"]["order_differs_between_quantities"], "of",
          s["e2"]["contrasts_with_two_classes_under_a_shared_condition"])
    if "agreement" in out:
        print("decisions", out["agreement"]["decisions"])


if __name__ == "__main__":
    main()
