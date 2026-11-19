"""Recount designs and recompute paired errors from the edition-specific derived data."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/revision"
RESULTS = ROOT / "results/revision"


def read(name):
    return json.loads((DATA / name).read_text())


def save(name, value):
    (RESULTS / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def unique(items):
    identifiers = [x for x in items]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Repeated record identity")
    return set(identifiers)


def family_groups(studies, links):
    # Only studies in this population can connect two component groups.
    groups = [{sid} for sid in sorted(studies)]
    for link in links:
        linked = set(link["works"])
        joined = [g for g in groups if linked & g]
        if joined:
            groups = [g for g in groups if not linked & g] + [set.union(*joined)]
    return sorted(sorted(g) for g in groups)


def members(tests, links):
    ids = sorted(t["id"] for t in tests)
    works = sorted({t.split("-")[0] for t in ids})
    families = family_groups(works, links)
    return dict(designs=len(ids), works=len(works), linked_groups=len(families),
                design_ids=ids, work_ids=works, known_link_groups=families)


def denominators(works, links):
    known = [w for w in works if w["eligibility_status"] == "documented eligible design"]
    uncertain = [w for w in works if w["eligibility_status"] == "contested"]
    cats = read("eligibility_rules.json")["denominators"]
    result = {}
    for category, definition in cats.items():
        def matching(population):
            return [t for w in population for t in w["tests"]
                    if any(category in o["groups"] for o in t["observables"])]
        fitted = matching(known)
        possible = matching(uncertain)
        counted = members(fitted, links)
        counted.update(rule=definition, contested_additions=members(possible, links))
        counted["observable_members"] = {
            t["id"]: [o["quantity"] for o in t["observables"] if category in o["groups"]] for t in fitted}
        result[category] = counted

    union = [t for w in known for t in w["tests"]
             if {"coupled_wmles", "rans_comparison"} & set(t["groups"])]
    by_baseline = defaultdict(list)
    for test in union:
        by_baseline[test["baseline_design"]].append(test)
    assert sum(len(r) for r in by_baseline.values()) == len(union)
    return dict(rules="eligibility_rules.json", unit="One source-located comparative series. Repeated stations, levels, observables and exposures can share a run. Record groups are descriptive and overlap.",
                scope="These are all-regime documentary counts by type. A strict incompressible smooth-wall success or failure fraction is not estimated. Design labels describe the identified comparison, not all calculations a paper could have run.",
                disposition=dict(Counter(w["eligibility_status"] for w in works)),
                by_historical_cohort={c: dict(Counter(w["eligibility_status"] for w in works
                    if w["historical_cohort"] == c)) for c in sorted({w["historical_cohort"] for w in works})},
                contested={w["study_id"]:w["reason"] for w in uncertain},
                excluded={w["study_id"]:w["reason"] for w in works if w["eligibility_status"]=="excluded"},
                missing_archived_full_text=[w["study_id"] for w in works if w["access_status"] != "Full archived source inspected."],
                evidence_by_type=result, baseline_availability={
                    "population":members(union,links), "by_design":{k:members(v,links) for k,v in sorted(by_baseline.items())},
                    "meaning":"Every eligible coupled LES/RANS series is at risk of lacking a within-setting wall-treatment alternative, including otherwise eligible single-treatment and grid-refinement series. Multiple baselines or controls in a series need observable-specific inspection in source_dispositions.json. The categories describe the principal comparison, and never assign an error direction to an absent baseline."})


def delta(y0, y1, ref):
    return [round(abs(a-r)-abs(b-r), 8) for b,a,r in zip(y0,y1,ref)]


def classify(d):
    if min(d)<0<max(d):
        return "opposite"
    if max(d)<0:
        return "both closer"
    if min(d)>0:
        return "both farther"
    return "includes tie"


def hill_results(source, links):
    rows = []
    for p in source["matched"]:
        ranking = {}
        for name,ref in p["reference_x_over_H"].items():
            if p["baseline_x_over_H"] is not None:
                d = delta(p["baseline_x_over_H"], p["alternative_x_over_H"], ref)
                ranking[name] = dict(delta_error_over_H=d, nominal_rank=classify(d))
            else:
                ranking[name] = dict(nominal_rank="crossing absent in baseline")
        ranks = {v["nominal_rank"] for v in ranking.values()}
        rows.append(dict(study_id=p["study_id"],condition=p["condition"], baseline=p["baseline"],
                         alternative=p["alternative"], ranks_by_reference=ranking,
                         category=ranks.pop() if len(ranks)==1 else "depends on reference"))
    works={r["study_id"] for r in rows}
    return dict(rule=source["rule"], units="x/H. Negative change means smaller absolute error using the same reference within each observable.",
                works=sorted(works), known_link_groups=family_groups(works,links), design_settings=len(rows),
                outcomes=dict(Counter(r["category"] for r in rows)), rows=rows,
                precision="These are ranks of printed point estimates. Different significant figures, benchmark choices and unequal averaging windows affect their interpretation; a source reporting 0.2 does not warrant treating this as an exact separation coordinate.")


def coordinates(name):
    with (DATA / "measurements" / name).open(newline="") as stream:
        return [{k:float(v) for k,v in row.items()} for row in csv.DictReader(stream)]


def errors(rows, ref, eq, alt):
    if not rows:
        raise ValueError("Comparison support is empty")
    first = mean(abs(r[eq] - r[ref]) for r in rows)
    second = mean(abs(r[alt] - r[ref]) for r in rows)
    return dict(n=len(rows), baseline_mae=first, alternative_mae=second, change=second-first)


def paired_results(links):
    velocity = coordinates("P31_Fig12c_DSM.csv")
    vcols = ("PIV_U_over_Uinf", "EQWM_DSM_U_over_Uinf", "RLWM_DSM_U_over_Uinf")
    pcols = ("Cp_experiment","Cp_EQWM","Cp_RLWM")
    pressure = [r for r in coordinates("P31_Fig11c_markers.csv") if r["x_over_L"]>.2]
    bump = dict(common_velocity=errors(velocity,*vcols), outer_velocity=errors([r for r in velocity if r["y_over_L"]>.02],*vcols),
                recovery_pressure=errors(pressure,*pcols), pressure_stations_worsening=sum(abs(r[pcols[2]]-r[pcols[0]])>abs(r[pcols[1]]-r[pcols[0]]) for r in pressure))
    crest=read("measurements/bump_crest_recovery.json")["crest_peaks"]
    bump["crest_friction_error_change_1000Cf"]=delta([crest["EQWM"]["1000Cf"]],[crest["RLWM"]["1000Cf"]],[crest["Gray_max_marker"]["1000Cf"]])[0]
    plate = {}
    for label,src in (("1000Cf","P23_Fig6_Cf_times1000.csv"), ("minus_Cp","P23_Fig6_minus_Cp.csv")):
        plate[label]=errors(coordinates(src), "experiment","DSM_EQ","BFM")
    channel = []
    for row in read("channel_scheme_table.json")["tables"]:
        for j,scheme in enumerate(("linear","LUST")):
            fields=[j,j+2]
            values=[[row[key][i] for i in fields] for key in ("no_wall_model","spalding")]
            change=delta(*values,[0,0])
            channel.append(dict(scheme=scheme,SGS=row["closure"],no_wall_model=values[0],spalding=values[1],
                                delta_absolute_error_percentage_points=change,direction=classify(change)))
    walls = {}
    for wall,record in read("he_profiles.json")["walls"].items():
        walls[wall]={}
        for q,x in record["quantities"].items():
            walls[wall][q]={}
            for support in ("full","trimmed_5pct_each_end"):
                stats=x[support]
                walls[wall][q][support]={m:stats["two_scale"][m]-stats["scalable"][m] for m in ("rmse","mae")}

    sst = {}
    for wall,record in read("he_profiles.json")["sst_comparison"]["walls"].items():
        sst[wall]={}
        for q,x in record["quantities"].items():
            sst[wall][q]={support:{m:x[support]["two_scale"][m]-x[support]["all_y_plus"][m]
                                for m in ("rmse","mae")} for support in ("full","trimmed_5pct_each_end")}
    step=read("dupuy_table5.json")
    m=step["magnitude"]; x=step["streamwise_component"]
    integral=dict(law_to_four=[m[3]-step["baseline_magnitude"], x[3]-step["baseline_streamwise_component"]],
                  four_to_five=[m[4]-m[3], x[4]-x[3]])
    return dict(convention="Alternative error minus baseline error within output. Errors retain the output’s own units. Signs are nominal unless joint uncertainty is available.",
                fixed_flow_channel=channel, natural_convection=walls, natural_convection_SST=sst, step_integral_change=integral, fine_DSM_bump=bump,
                building_block_bump_all_measured_stations=plate, periodic_hill_tables=hill_results(read("hill_table_population.json"),links))


def main():
    works = read("source_dispositions.json")["records"]
    p = read("paired_readings.json")["records"]
    source_ids=unique(w["study_id"] for w in works)
    frame=unique(w["study_id"] for w in read("historical_source_manifest.json"))
    assert source_ids==frame and len(frame)==115
    tests = unique(t["id"] for w in works for t in w["tests"])
    for q in p:
        for side in ("first","second"):
            assert set(q[side]["design_ids"]) <= tests
            assert q[side]["runs"] and q[side]["criterion"] and q[side]["reference"] and q[side]["source_location"]
    old = json.loads((ROOT/"data/contrast_pairs.json").read_text())
    assert unique(r["pair_id"] for r in p)==unique(r["pair_id"] for r in old)
    assert len(p)==79 and sum(r["original_nomination"] for r in p)==10
    assert len({r["study_id"] for r in p})==20
    links=read("study_families.json")["links"]
    assert all(set(link["works"])<=source_ids for link in links)
    ledger = denominators(works,links)
    exposure=read("transfer_exposure.json")
    listed=exposure["records"]
    assert unique(r["design_id"] for r in listed)<=tests
    certified=ledger["evidence_by_type"]["independent_transfer"]["design_ids"]
    assert sorted(r["design_id"] for r in listed if r["status"]=="qualified")==certified
    ledger["selection_sensitivity"]={"scope":exposure["estimand"],"by_status":{
        st:{"design_ids":sorted(r["design_id"] for r in listed if r["status"]==st),
            "work_ids":sorted({r["design_id"].split("-")[0] for r in listed if r["status"]==st})}
        for st in sorted({r["status"] for r in listed})}}
    paired = paired_results(links)
    assert paired["fine_DSM_bump"]["common_velocity"]["n"]==120
    assert paired["fine_DSM_bump"]["common_velocity"]["change"]>0>paired["fine_DSM_bump"]["outer_velocity"]["change"]
    assert paired["fine_DSM_bump"]["pressure_stations_worsening"]==paired["fine_DSM_bump"]["recovery_pressure"]["n"]==10
    assert all(c["direction"] == ("opposite" if c["scheme"]=="linear" else "both closer") for c in paired["fixed_flow_channel"])
    for wall,v in paired["natural_convection"].items():
        for q in v:
            for support, metrics in v[q].items():
                for d in metrics.values():
                    # The left-baffle heat MAE changes sign on trimmed support only.
                    if wall=="baffleLeft" and q.startswith("q") and support=="trimmed_5pct_each_end":
                        assert metrics["rmse"]<0<metrics["mae"]
                    else:
                        assert (d>0)==(wall=="baffleRight" and q.startswith("q"))
    second=read("reader_agreement.json")
    verdict=second["memberships"]["decision_rule_verdict"]
    assert set(ledger["evidence_by_type"])<=set(verdict)
    ledger["second_reading"]={
        "scope":second["scope"],
        "status_by_type":{k:verdict[k]["status"] for k in ledger["evidence_by_type"]},
        "use":"Counts for a type whose status is not quotable are first-reading counts. Do not quote them. "
              "Series counts depend on how finely a paper is split and are not reproducible between readings; quote works.",
        "design_counts_among_36_works_read_twice":second["memberships"]["design_counts_among_works_read_twice"]["all_designs"]}
    vocabulary=list(read("paired_readings.json")["category_counts"])
    assert all(r["adjudication"] in vocabulary for r in p)
    ledger["historical_pair_categories"]={c:sum(r["adjudication"]==c for r in p) for c in vocabulary}
    save("eligible_units.json",ledger)
    save("paired_error_changes.json",paired)
    print(f"Checked {len(works)} works, {len(tests)} design series and {len(p)} historical pairings.")


if __name__=="__main__":
    main()
