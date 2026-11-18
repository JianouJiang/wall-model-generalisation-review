#!/usr/bin/env python3
"""Design-based audit with complete study eligibility sensitivity.

The unit is a study's selected treatment. Test rows are coded comparison units,
not independent simulations. Outcome signs do not enter the design criterion.
This analysis describes the identified source versions, not the prevalence of
validation in the latest published literature.
"""
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('scope', ROOT/'code/analyse_scope.py')
scope = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scope)

def record_states(tests, include_unknown):
    # Deduplicate by the design information actually used. Outcome disagreements
    # cannot create or remove a transfer design.
    alternatives=[]
    for t in tests:
        fs=[(k,v) for k,v in t.get('alternatives',{}).items()
            if k in ('scope','calibration_family','observable_status','cause_exercised')]
        states=set()
        for values in itertools.product(*(v for k,v in fs)):
            row=dict(t);row.update(zip((k for k,v in fs),values))
            states.add((scope.in_scope(row,include_unknown), scope.coupled(row),scope.exposure(row)))
        alternatives.append(states)
    # Fold the union of row properties. This avoids an exponential Cartesian
    # enumeration while preserving every attainable study-level state.
    states={(False,False,False,False)}
    for rows in alternatives:
        states={(eligible or ins, coupled or (ins and c), exposed or (ins and e=='yes'),
                 unknown or (ins and e=='unknown'))
                for eligible,coupled,exposed,unknown in states for ins,c,e in rows}
    return states

def study_states(c, include_unknown):
    return set().union(*(record_states(ts,include_unknown)
                        for ts in [c['tests']]+c.get('alternative_records',[])))

def bound(states, predicate):
    return {'confirmed':sum(all(predicate(s) for s in ss) for ss in states.values()),
            'possible':sum(any(predicate(s) for s in ss) for ss in states.values())}

def analyse(claims, include_unknown):
    states={c['study_id']:study_states(c,include_unknown) for c in claims}
    groups={}
    for group in ('pooled','new','pilot'):
        ids=[c['study_id'] for c in claims if group=='pooled' or c['set']==group]
        st={sid:states[sid] for sid in ids}
        groups[group]={
            'candidate_studies':len(ids),
            'eligible':bound(st,lambda s:s[0]),
            'coupled_validation_in_scope':bound(st,lambda s:s[1]),
            'documented_transfer_design':bound(st,lambda s:s[2]),
            'design_uncertain_without_documented_transfer':bound(st,lambda s:s[0] and not s[2] and s[3]),
            'no_documented_transfer_design_in_coded_rows':bound(st,lambda s:s[0] and not s[2] and not s[3]),
        }
    return {'groups':groups,'study_states':{sid:[list(x) for x in sorted(ss)] for sid,ss in states.items()}}

def main():
    original=json.loads((ROOT/'data/test_codings.json').read_text())
    revised=json.loads((ROOT/'data/revision/test_codings.json').read_text())
    assert len({c['study_id'] for c in revised})==len(revised)==84
    extra=[c for c in revised if c['study_id'] in ('P16','N444')]
    scenarios={
        'historical_82_strict':analyse(original,False),
        'historical_82_unknown_included':analyse(original,True),
        'historical_84_unknown_included':analyse(original+extra,True),
        'revised_84_strict':analyse(revised,False),
        'revised_84_unknown_included':analyse(revised,True),
    }
    # Independent parity with the historical enumeration for the original cohort.
    for include,label in [(False,'historical_82_strict'),(True,'historical_82_unknown_included')]:
        reference={c['study_id']:scope.claim_result(c['tests'],include) for c in original}
        for c in original:
            before={s[1]=='yes' for s in reference[c['study_id']]['design_states']}
            after={s[2] for s in scenarios[label]['study_states'][c['study_id']]}
            assert before==after,c['study_id']
    allcoupled={c['study_id'] for c in revised if any(scope.coupled(t) for t in c['tests'])}
    out={'status':'Historical diagnostic only: intermediate 84-study recalculation. Wider eligibility inconsistencies prevent a repaired population denominator. No aggregate from this file is a current manuscript finding.',
         'unit':'One selected treatment per study; comparison rows are not independent simulations.',
         'uncertainty':'Ranges cover alternative codings. Literal unknown design information remains unknown, not a hidden favourable or adverse result. These are not confidence intervals.',
         'source_version_limit':'Census describes the exact archived source copies. Only the specifically recoded sources have been checked against the published version; the count is not an estimate for all current journal articles.',
         'studies_with_any_coupled_validation_regardless_of_scope':len(allcoupled),
         'scenarios':scenarios}
    (ROOT/'results/revision').mkdir(exist_ok=True)
    (ROOT/'results/revision/design_audit.json').write_text(json.dumps(out,indent=2)+'\n')
    for label,v in scenarios.items():
        g=v['groups']['pooled']
        print(label, 'eligible',g['eligible'],'documented transfer',g['documented_transfer_design'])
    # Structural tests for defects that originally changed the interpretation.
    p16=next(c for c in revised if c['study_id']=='P16')
    assert all(not s[2] for s in study_states(p16,True))
    assert all(s[0] for s in study_states(p16,True))
    ag=next(c for c in revised if c['study_id']=='N418')
    assert any(scope.coupled(t) for t in ag['tests'])
    assert next(t for t in ag['tests'] if t['test_id']=='N418-R03')['result_flag']=='improvement shown'
    assert not any(t['test_id']=='N418-T09' for t in ag['tests'])
    assert all(not scope.in_scope(t,True) for t in ag['tests'] if t['scope']=='no: compressible')
    print('Historical parity and correction invariants passed.')

if __name__=='__main__':
    main()
