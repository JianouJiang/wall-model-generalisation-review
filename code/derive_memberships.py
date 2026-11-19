"""Derive the three fact-based evidence groups from the recorded facts and check the stored values.

Inputs (data/revision): wall_change_contrasts.json, constitutive_facts.json, transfer_exposure.json,
source_dispositions.json. The rule text is stored in wall_change_contrasts.json["rule"]["text"].
Every membership, baseline label and transfer status in the data must equal the value recomputed here.
Output: results/revision/derived_memberships.json. Standard library only (python3 -I).
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/revision"
RESULTS = ROOT / "results/revision"

COUPLED = {"coupled LES", "coupled hybrid RANS-LES", "coupled RANS"}
WALL_VARIANTS = {"different model", "same model, different imposition", "same model, different input",
                 "same model, different parameter"}
FACTORS = ("grid", "outer_closure", "numerics", "forcing", "reynolds_number", "domain")
SOLVER_CLASSES = {"LES", "hybrid RANS-LES", "RANS"}
LABEL = {
    "member": "identified within-setting alternative",
    "upper": "within-setting alternative with a control unreported",
    "varied": "whole-system or multiple simultaneous changes",
    "noref": "alternative compared without a quantitative common reference",
    "same": "same wall treatment: grid, Reynolds number, numerical solution or discretisation varies",
    "single": "no distinct wall-treatment baseline identified",
    "na": "not applicable (not a coupled LES or RANS series)",
}


def read(name):
    return json.loads((DATA / name).read_text())


def tier(c):
    """Rule section A. Returns 'strict', 'broad' (broad and not strict), 'upper' or 'none', and why not."""
    why = []
    if c["feedback"] not in COUPLED:
        why.append("prescribed input" if c["feedback"] == "prescribed input" else "no coupled LES, hybrid or RANS feedback")
    if c["variant_type"] not in WALL_VARIANTS:
        why.append("numerical-solution or discretisation variant")
    if not c["hydrodynamic_observables"]:
        why.append("thermal observables only" if c.get("thermal_observables") else "no hydrodynamic observable")
    if c["reference_comparison"] not in ("tabulated", "plotted"):
        why.append("no quantitative common reference")
    levels = [c["factors"][f] for f in FACTORS]
    if "varied" in levels:
        why.append("factor varied: " + ", ".join(f for f in FACTORS if c["factors"][f] == "varied"))
    if why:
        return "none", why
    if "unreported" in levels:
        return "upper", ["factor unreported: " + ", ".join(f for f in FACTORS if c["factors"][f] == "unreported")]
    return ("strict" if c["variant_type"] == "different model" else "broad"), []


def label(test, contrasts):
    """Derived baseline label of one design series: the first rule that applies."""
    coupled = [c for c in contrasts if c["feedback"] in COUPLED]
    if test["solver_class"] not in SOLVER_CLASSES and not coupled:
        return LABEL["na"]
    found = [tier(c) for c in coupled]
    names = {t for t, _ in found}
    reasons = [r for _, rs in found for r in rs]
    if names & {"strict", "broad"}:
        return LABEL["member"]
    if "upper" in names:
        return LABEL["upper"]
    if any(r.startswith("factor varied") for r in reasons):
        return LABEL["varied"]
    if "no quantitative common reference" in reasons:
        return LABEL["noref"]
    if "numerical-solution or discretisation variant" in reasons:
        return LABEL["same"]
    if str(test["wall_change"].get("if_no_contrast") or "").startswith("sweep"):
        return LABEL["same"]
    return LABEL["single"]


def status(row):
    """Rule section C. A fact that stayed disputed after the settlement gives 'selection unresolved' (agreement plan, fixed in advance)."""
    if row.get("disputed_after_settlement"):
        return "selection unresolved"
    if row["variants_compared_on_target"] or any(s["uses_target"] == "yes" for s in row["selection_decisions"]):
        return "partly exposed"
    if row["frozen_external"] or row["holdout_statement"]:
        return "qualified"
    return "selection unresolved"


def main():
    works = read("source_dispositions.json")["records"]
    contrast_file = read("wall_change_contrasts.json")
    contrasts = contrast_file["records"]
    assert hashlib.sha256(contrast_file["rule"]["text"].encode()).hexdigest() == contrast_file["rule"]["sha256_of_rule_file"]
    eligible = {w["study_id"] for w in works if w["eligibility_status"] == "documented eligible design"}
    boundary = sorted(w["study_id"] for w in works if w.get("scope_boundary") and w["study_id"] in eligible)
    by_work, by_design, outside_sublayer = {}, {}, {}
    for c in contrasts:
        t, why = tier(c)
        assert c["derived"] == {"tier": t, "reasons": why}, c["contrast_id"]
        assert c["work_counted"] == (c["study_id"] in eligible), c["contrast_id"]
        assert c.get("sublayer_class") in (None, "U", "S", "N"), c["contrast_id"]
        by_work.setdefault(c["study_id"], []).append(t)
        if c.get("sublayer_class") != "S":       # the wall-normal grid of this contrast does not reach the viscous sublayer
            outside_sublayer.setdefault(c["study_id"], []).append(t)
        by_design.setdefault(c["design_id"], []).append(c)
    order = ("strict", "broad", "upper")
    reach = {"strict": {"strict"}, "broad": {"strict", "broad"}, "upper": {"strict", "broad", "upper"}}

    def member(sid, level):
        return sid in eligible and bool(set(by_work.get(sid, [])) & reach[level])

    def member_narrow(sid, level):
        """Member without scope-boundary works and without contrasts on a grid that reaches the viscous sublayer."""
        return sid in eligible and sid not in boundary and bool(set(outside_sublayer.get(sid, [])) & reach[level])

    labels = Counter()
    label_works = {}
    for w in works:
        sid = w["study_id"]
        assert w["wall_change_membership"] == {k: member(sid, k) for k in order}, sid
        for t in w["tests"]:
            mine = by_design.get(t["id"], [])
            assert sorted(c["contrast_id"] for c in mine) == sorted(t["wall_change"]["contrast_ids"]), t["id"]
            assert t["baseline_design"] == label(t, mine), t["id"]
            names = {tier(c)[0] for c in mine}
            best = next((k for k in order if k in names), "none")
            assert t["wall_change"]["tier"] == best, t["id"]
            assert ("controlled_wall_change" in t["groups"]) == bool(names & {"strict", "broad"}), t["id"]
            if sid in eligible and {"coupled_wmles", "rans_comparison"} & set(t["groups"]):
                labels[t["baseline_design"]] += 1
                label_works.setdefault(t["baseline_design"], set()).add(sid)

    def listing(ids):
        ids = sorted(ids)
        return dict(works=len(ids), works_without_scope_boundary=len([i for i in ids if i not in boundary]), work_ids=ids)

    change = {k: listing(s for s in eligible if member(s, k)) for k in order}
    for k in order:
        narrow = sorted(s for s in eligible if member_narrow(s, k))
        change[k].update(works_without_scope_boundary=len(narrow),
                         work_ids_dropped_without_scope_boundary=sorted(set(change[k]["work_ids"]) - set(narrow)))
    reasons = Counter(r.split(":")[0] for c in contrasts if c["work_counted"] for r in tier(c)[1])

    cons = read("constitutive_facts.json")
    members = []
    for r in cons["records"]:
        is_member = r["study_id"] in eligible and any(
            c["restriction"] and c["reference_only_paired_data"] and c["violation_statistic"] for c in r["candidates"])
        assert r["member"] == is_member, r["study_id"]
        if is_member:
            members.append(r["study_id"])
    assert sorted(members) == cons["members"]
    assert all(w["constitutive_constraint_member"] == (w["study_id"] in members) for w in works)

    transfer = read("transfer_exposure.json")
    rows = transfer["records"]
    for r in rows:
        assert r["status"] == status(r), r["transfer_id"]
        assert r["work_counted"] == (r["study_id"] in eligible), r["transfer_id"]
    counted = [r for r in rows if r["work_counted"]]
    names = ("qualified", "partly exposed", "selection unresolved")

    def split(sel):
        tests = Counter(r["status"] for r in sel)
        return dict(tests={s: tests.get(s, 0) for s in names}, total_tests=len(sel),
                    works={s: len({r["study_id"] for r in sel if r["status"] == s}) for s in names},
                    total_works=len({r["study_id"] for r in sel}),
                    tests_not_shown_to_be_exposed=[tests.get("qualified", 0), tests.get("qualified", 0) + tests.get("selection unresolved", 0)])

    whole = split(counted)
    assert transfer["split_of_tests"] == {k: v for k, v in whole["tests"].items() if v}
    assert transfer["not_shown_to_be_exposed"] == whole["tests_not_shown_to_be_exposed"]
    fitted = sorted(w["study_id"] for w in works if w["has_fitted_treatment"] and w["study_id"] in eligible)

    five = {g: sorted(w["study_id"] for w in works if w["study_id"] in eligible and any(g in t["groups"] for t in w["tests"]))
            for g in ("prescribed_input", "coupled_wmles", "rans_comparison", "system_benchmark", "thermal")}
    out = dict(
        rule=dict(fixed_at=contrast_file["rule"]["fixed_at"], sha256=contrast_file["rule"]["sha256_of_rule_file"]),
        population=dict(works=len(works), eligible_works=len(eligible), scope_boundary_works=boundary,
                        scope_boundary_by_kind=dict(Counter(w["scope_boundary"]["kind"] for w in works if w["study_id"] in boundary)),
                        eligible_works_without_scope_boundary=len(eligible) - len(boundary),
                        contrasts_on_a_sublayer_resolving_grid=sorted(c["contrast_id"] for c in contrasts if c.get("sublayer_class") == "S" and c["work_counted"])),
        matched_wall_treatment_change=dict(
            meaning="Works with at least one within-paper contrast of wall treatments in a coupled calculation, compared quantitatively with a reference on a hydrodynamic quantity. Strict: a different model with all six controls stated fixed. Broad (the group): also another imposition, input or parameter of one model. Upper bound: also contrasts with a control unreported.",
            tiers=change, contrasts_in_counted_works=dict(Counter(tier(c)[0] for c in contrasts if c["work_counted"])),
            reasons_among_non_member_contrasts=dict(reasons)),
        baseline_labels=dict(coupled_design_series=sum(labels.values()),
                             by_label={k: dict(designs=labels[k], works=len(label_works[k])) for k in sorted(labels)}),
        constitutive_constraint=dict(members=sorted(members), works=len(members),
                                     works_without_scope_boundary=len([m for m in members if m not in boundary]),
                                     works_with_a_candidate=len({r["study_id"] for r in cons["records"] if r["study_id"] in eligible})),
        transfer=dict(works_with_fitted_treatment=len(fitted), all_counted_works=whole,
                      without_scope_boundary=split([r for r in counted if r["study_id"] not in boundary])),
        five_typed_groups={g: dict(works=len(v), works_without_scope_boundary=len([i for i in v if i not in boundary])) for g, v in five.items()})
    (RESULTS / "derived_memberships.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print("Derived memberships agree with the stored values:",
          {k: v["works"] for k, v in change.items()}, "constitutive", len(members), "transfer", whole["tests"])


if __name__ == "__main__":
    main()
