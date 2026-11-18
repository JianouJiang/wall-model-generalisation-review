#!/usr/bin/env python3
"""Recompute claim categories and exposure bounds from exported test codings.

Only the existing 82-claim cohort is evaluated. This sensitivity does not decide
the eligibility of studies excluded entirely for unknown scope. See the audit.
"""
import csv
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAVOURABLE = {
    'improvement shown', 'preserved accuracy',
    'agreement with reference (no matched comparison)',
}
ADVERSE = {
    'regression', 'improvement not shown',
    'disagreement with reference (no matched comparison)',
}
FIELDS = ('scope', 'calibration_family', 'observable_status', 'cause_exercised', 'result_flag')
CATEGORIES = ('1a', '1b', '2', '3', '4', '5', '6', '7')


def low(value):
    return value.strip().lower() if isinstance(value, str) else value


def in_scope(test, include_unknown=False):
    return low(test.get('scope')) in (('yes', 'unknown') if include_unknown else ('yes',))


def coupled(test):
    return 'coupled' in low(test.get('mode') or '')


def exposure(test):
    """Could this test have exposed a failure to transfer, under the coded rule?"""
    mode = low(test.get('mode') or '')
    family = low(test.get('calibration_family') or '')
    observable = low(test.get('observable_status') or '')
    cause = low(test.get('cause_exercised') or '')
    conditions = [
        ('coupled' in mode) if mode else None,
        (family == 'outside') if family in ('inside', 'outside') else None,
        (observable == 'free') if observable in ('fixed', 'free') else None,
        (cause == 'yes') if cause in ('yes', 'no') else None,
    ]
    if all(c is True for c in conditions):
        return 'yes'
    if any(c is False for c in conditions):
        return 'no'
    return 'unknown'


def category(tests):
    if not tests:
        return '7', 'no', 'no'
    exposing = [exposure(t) for t in tests]
    flags = [low(t.get('result_flag') or 'none') for t in tests]
    favourable = any(e == 'yes' and f in FAVOURABLE for e, f in zip(exposing, flags))
    adverse = any(coupled(t) and f in ADVERSE for t, f in zip(tests, flags))
    improvement = any(e == 'yes' and f == 'improvement shown' for e, f in zip(exposing, flags))
    if favourable and adverse:
        result = '2'
    elif favourable:
        result = '1a' if improvement else '1b'
    elif adverse:
        result = '3'
    elif 'yes' in exposing:
        result = '4'
    elif 'unknown' in exposing:
        result = '5'
    else:
        result = '6'
    return result, 'yes' if favourable else 'no', 'yes' if adverse else 'no'


def alternatives(tests, include_unknown):
    """Enumerate independent coded alternatives, deduplicating equivalent rows."""
    per_row = []
    for test in tests:
        cells = [(f, test['alternatives'][f]) for f in FIELDS if f in test.get('alternatives', {})]
        representatives = {}
        for values in itertools.product(*(values for _, values in cells)):
            row = dict(test)
            row.update(zip((f for f, _ in cells), values))
            signature = (in_scope(row, include_unknown), coupled(row), exposure(row), low(row.get('result_flag') or 'none'))
            representatives.setdefault(signature, row)
        per_row.append(list(representatives.values()))
    yield from itertools.product(*per_row)


def claim_result(tests, include_unknown):
    outcomes = []
    states = set()
    for rows in alternatives(tests, include_unknown):
        selected = [t for t in rows if in_scope(t, include_unknown)]
        if not selected:
            scope = [low(t.get('scope') or '') for t in rows]
            why = 'X4' if scope and all(s.startswith('no') for s in scope) else 'scope unknown'
            outcomes.append(('out of scope: ' + why, 'no', 'no', 0))
            states.add(('out of scope', 'none', False))
            continue
        cat, favourable, adverse = category(selected)
        outcomes.append((cat, favourable, adverse, len(selected)))
        ex = [exposure(t) for t in selected]
        ex_state = 'yes' if 'yes' in ex else ('unknown' if 'unknown' in ex else 'no')
        adv_ex = any(e == 'yes' and low(t.get('result_flag') or 'none') in ADVERSE for e, t in zip(ex, selected))
        states.add((cat, ex_state, adv_ex))
    result = {}
    for i, name in enumerate(('category', 'F', 'A', 'rows_in_scope')):
        values = sorted({row[i] for row in outcomes})
        result[name] = values[0] if len(values) == 1 else 'undetermined'
        if len(values) > 1 and name in ('category', 'rows_in_scope'):
            result[name + '_alternatives'] = values
    result['design_states'] = [list(state) for state in sorted(states, key=str)]
    return result


def bounds(results, predicate):
    values = [[predicate(state) for state in result['design_states']] for result in results]
    return {'confirmed': sum(all(v) for v in values), 'possible': sum(any(v) for v in values)}


def summarise(results):
    values = list(results.values())
    categories = Counter(c['category'] for c in values)
    exposed = bounds(values, lambda s: s[1] == 'yes')
    in_scope_count = bounds(values, lambda s: s[0] != 'out of scope')
    return {
        'claims': len(values),
        'categories': {k: categories[k] for k in CATEGORIES},
        'undetermined': categories['undetermined'],
        'exposed_claims': exposed,
        'claims_in_scope': in_scope_count,
        'category_1': bounds(values, lambda s: s[0] in ('1a', '1b')),
        'flag_F': bounds(values, lambda s: s[0] in ('1a', '1b', '2')),
        'flag_A': bounds(values, lambda s: s[0] in ('2', '3')),
        'fewer_than_half_exposed': 2 * exposed['possible'] < len(values)
            and 2 * exposed['possible'] < in_scope_count['confirmed'],
    }


def main():
    claims = json.loads((ROOT / 'data/test_codings.json').read_text())
    expected = json.loads((ROOT / 'data/expected_claim_results.json').read_text())
    results = {
        variant: {c['study_id']: claim_result(c['tests'], include) for c in claims}
        for variant, include in [('baseline', False), ('include_unknown', True)]
    }
    assert results == expected, 'Recalculation differs from the supplied reference results.'
    main_claims = list(csv.DictReader((ROOT / 'data/claims.csv').open()))
    assert len(main_claims) == len(claims) == 82
    for c in main_claims:
        calculated = results['baseline'][c['study_id']]
        assert str(calculated['category']) == c['category'], c['study_id']
        assert calculated['F'] == c['flag_F'] and calculated['A'] == c['flag_A'], c['study_id']
    summary = {
        'cohort': 'Existing 82 claims only; entirely scope-excluded studies are not reintroduced.',
        'baseline': {}, 'include_unknown': {},
    }
    for variant in results:
        for group in ('pooled', 'new', 'pilot'):
            ids = {c['study_id'] for c in claims if group == 'pooled' or c['set'] == group}
            summary[variant][group] = summarise({sid: r for sid, r in results[variant].items() if sid in ids})
    rows = [t for c in claims for t in c['tests']]
    summary['coded_test_rows'] = len(rows)
    summary['unknown_scope_rows'] = sum(low(t.get('scope')) == 'unknown' for t in rows)
    summary['unknown_scope_coupled_rows'] = sum(low(t.get('scope')) == 'unknown' and coupled(t) for t in rows)
    summary['claims_with_literal_unknown_scope_rows'] = [c['study_id'] for c in claims if any(low(t.get('scope')) == 'unknown' for t in c['tests'])]
    summary['category_changes'] = [
        {'study_id': sid, 'baseline': results['baseline'][sid]['category'], 'include_unknown': result['category']}
        for sid, result in results['include_unknown'].items()
        if result['category'] != results['baseline'][sid]['category']
    ]
    summary['affected_mixed_claims'] = [
        c['study_id'] for c in claims
        if any(low(t.get('scope')) == 'unknown' or 'unknown' in t.get('alternatives', {}).get('scope', []) for t in c['tests'])
        and results['include_unknown'][c['study_id']]['category'] == '2'
    ]
    summary['quantity_contrast'] = {
        'baseline': {'quantity_only': 9, 'mixed_claims': 18},
        'include_unknown': {'quantity_only': None, 'mixed_claims': 19},
        'status': 'Needs a fresh pair-level assessment across all affected mixed claims, not just the newly mixed claim.',
    }
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    (out / 'scope_sensitivity.json').write_text(json.dumps(summary, indent=2) + '\n')
    (out / 'claim_results.json').write_text(json.dumps(results, indent=2) + '\n')
    print('Verified 82 claim results in both scope variants against the reference snapshot.')
    print('Exposure:', summary['baseline']['pooled']['exposed_claims'], '->', summary['include_unknown']['pooled']['exposed_claims'])
    print('Category changes:', summary['category_changes'])


if __name__ == '__main__':
    main()
