#!/usr/bin/env python3
"""Check the current critical review without validating superseded census claims."""
import csv
import hashlib
import json
import math
import re
import subprocess
from itertools import product
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

ROOT=Path(__file__).resolve().parents[1]
M=ROOT/'manuscript'
main=(M/'main.tex').read_text()
parts=[main]+[(M/f).read_text() for f in ('evidence_table.tex','checklist_table.tex','methods_box.tex')]
alltext='\n'.join(parts)

def arguments(text,command):
    """Extract balanced mandatory arguments, including nested LaTeX commands."""
    values=[]
    for m in re.finditer(re.escape('\\'+command)+'\\{',text):
        i=m.end();start=i;level=1
        while level:
            if text[i]=='{' and text[i-1]!='\\':level+=1
            if text[i]=='}' and text[i-1]!='\\':level-=1
            i+=1
        values.append(text[start:i-1])
    return values

def words(s):
    s=re.sub(r'\\[A-Za-z]+(?:\{[^{}]*\})?', ' macro ',s)
    return len(re.findall(r"\S+",s))

def check_figure2(comparisons, plotted, support_by_id):
    panels = comparisons['figure_panels']
    keys = [key for panel in panels for key in panel['studies']]
    rows = {row['reference_key']: row for row in comparisons['rows']}
    assert len(panels) == 4 and all(len(p['studies']) == 2 for p in panels)
    assert len(keys) == len(set(keys)) == 8 and set(keys) == rows.keys()
    assert plotted['figure_panels'] == panels
    for row in rows.values():
        assert all(support_by_id[key]['figure_2_source_location'] == row['figure_source_location']
                   for key in row['support'])

    def example(key):
        return rows[key]['figure_example']

    channel = example('BaeKoumoutsakos2022')
    assert channel['friction_reynolds_number'] == 50000
    assert channel['training_height_wall_units'] == [150, 1200]
    assert [(m['dy_over_delta'], m['height_wall_units']) for m in channel['measurements']] == [(.01, 1000), (.05, 5000)]
    pairs = example('Mukha2025')['measurements']
    assert [(p['mesh'], p['coupled'], p['offline_mean']) for p in pairs] == [
        ('M1', .71, .06), ('M2', .76, .20), ('M3', -.54, -1.07)]
    sweep = example('Hayat2024preprint')
    assert sweep['sweep_degrees'] == [0, 35]
    assert [m['signs'] for m in sweep['measurements']] == [[None, -1], [1, -1], [-1, -1]]
    closures = example('LozanoDuranBae2023')['measurements']
    assert [(m['outer_closure'], m['stress_error']) for m in closures] == [
        ('Exact for the mean', 'Internal'), ('Dynamic Smagorinsky', 'Total'), ('Vreman', 'Total')]
    outer, wall = example('ZhouBae2024'), example('Agrawal2024')
    assert outer['length_reynolds_number'] == wall['length_reynolds_number'] == 2000000
    assert [(m['coefficient'], m['reversal']) for m in outer['measurements']] == [(.025, True), (.070, False)]
    assert [(m['model'], m['reversal']) for m in wall['measurements']] == [('Equilibrium', False), ('Sensor-based', True)]

    step = example('Dupuy2023graph')
    scale = step['digitisation']
    for trace in step['crossings']:
        (x1, y1), (x2, y2) = trace['bracketing_centres_px']
        y0 = scale['zero_stress_y_px']
        assert y2 < y0 < y1
        crossing = x1 + (y0-y1)*(x2-x1)/(y2-y1)
        distance = 14*(crossing-scale['x_at_zero_px'])/(scale['x_at_fourteen_px']-scale['x_at_zero_px'])
        assert round(distance, 1) == trace['x_over_hs_approx']
    assert [m['x_over_hs_approx'] for m in step['crossings']] == [4.7, 5.2, 6.0]
    diffuser = example('Jones2015')['measurements']
    assert [(m['cells_y'], m['recirculation']) for m in diffuser] == [(30, False), (50, True)]

def check_panel_style(comparisons):
    titles = {
        'fig1_loop': ['The coupled loop', 'Reversed layer', 'What each test sees'],
        'fig2_record': [panel['title'] for panel in comparisons['figure_panels']],
        'fig3_contrast': ['Backward-facing step with a graph wall model',
                          'Wall stress in a zero-pressure-gradient boundary layer'],
        'fig4_checklist': ['Agreement by choice', 'Cases by combination of matches'],
    }
    reference_offset = None
    for name, headings in titles.items():
        xml = subprocess.check_output(['pdftohtml', '-xml', '-i', '-fontfullname', '-noroundcoord',
                                       '-zoom', '1', '-stdout', str(ROOT/'figures'/f'{name}.pdf')])
        page = ElementTree.fromstring(xml).find('page')
        fonts = {f.get('id'): (f.get('family').split('+')[-1], float(f.get('size')), f.get('color'))
                 for f in page.findall('fontspec')}
        spans = {(''.join(t.itertext()).strip(), fonts[t.get('font')]): t for t in page.findall('text')}
        for panel, title in zip('abcd', headings):
            letter = spans[(panel, ('DejaVuSans-Bold', 10, '#000000'))]
            heading = spans[(title, ('DejaVuSans', 8, '#0b0b0b'))]
            offset = tuple(float(heading.get(k)) - float(letter.get(k)) for k in ('left', 'top'))
            if reference_offset is None:
                reference_offset = offset
            assert all(abs(a-b) < .03 for a, b in zip(offset, reference_offset)), (name, panel, offset)
    return sum(map(len, titles.values()))

def check_checklist_patterns(cases, keys, plotted):
    assert plotted['choice_order'] == ['Cause', 'Quantity class', 'Factor to vary']
    patterns = plotted['display_patterns']
    assert len(patterns) == 8
    assert {tuple(p['choices']) for p in patterns} == set(product((False, True), repeat=3))
    for pattern in patterns:
        ids = [c['case'] for c in cases if [c['agreement'][key] for key in keys] == pattern['choices']]
        assert pattern['case_ids'] == ids and pattern['count'] == len(ids)
    counts_by_degree = [sum(p['count'] for p in patterns if sum(p['choices']) == m) for m in range(4)]
    assert counts_by_degree == [0, 4, 6, 3]
    paired = json.loads((ROOT/'data/revision/checklist_choices.json').read_text())['cases']
    archived = {c['case']: c['agreement'] for c in cases}
    assert len(archived) == len(paired) == 13 and {r['case'] for r in paired} == set(archived)
    for row in paired:
        for field, key in zip(('cause', 'observable_class', 'factor_varied_alone'), keys):
            a, b = row['A'][field], row['B'][field]
            assert isinstance(a, str) and a.strip() and isinstance(b, str) and b.strip()
            assert (a == b) == archived[row['case']][key], (row['case'], field)
    other_matches = [r['case'] for r in paired if r['A']['observable_class'] == r['B']['observable_class'] == 'other']
    assert other_matches == ['K08']
    return counts_by_degree

def check_evidence_selection(comparisons, cases):
    data = ROOT / 'data'
    def read_csv(name):
        with (data / name).open(newline='') as source:
            return list(csv.DictReader(source))

    screened = {r['screen_id']: r for r in read_csv('search_records.csv')}
    frame = read_csv('revision/retrieval_frame.csv')
    study = {r['study_id']: r for r in read_csv('studies.csv')}
    assert len(set(r['screen_id'] for r in frame)) == len(frame) == 735
    assert all(r['screen_id'] in screened for r in frame)
    assert len(screened) == 2543
    logged = Counter(r['retrieval'] for r in frame)
    assert logged == {'no candidate route': 564, 'access refused': 28, 'unusable retrieval': 23, 'retrieved': 120}
    obtained = [r for r in frame if r['retrieval'] == 'retrieved']
    assert Counter(r['full_text_language_screen'] for r in obtained) == {'pass': 112, 'flagged': 8}
    retained = {r['study_id']: r for r in frame if r['study_id']}
    assert len(retained) == len(study) == 115 and retained.keys() == study.keys()
    for sid, r in retained.items():
        assert r['retrieval'] == 'retrieved'
        assert screened[r['screen_id']]['doi'].casefold() == study[sid]['doi'].casefold()
    doi = {s['doi'].casefold() for s in study.values()}
    assert len({r['journal_doi'].casefold() for r in comparisons['rows']} & doi) == 8

    rules = json.loads((data / 'revision/eligibility_rules.json').read_text())
    examples = json.loads((data / 'revision/eligibility_examples.json').read_text())['records']
    assert set(r['study_id'] for r in examples) == {'P05', 'N080', 'N054', 'N280', 'N626', 'P10'}
    for r in examples:
        assert study[r['study_id']]['doi'].casefold() == r['doi'].casefold()
        assert r['edition'] and r['regime_and_forcing'] and r['calibration_and_dependence']
        for t in r['tests']:
            assert t['source_location'] and t['comparison'] and t['limit']
            for obs in t['observables']:
                assert set(obs['groups']) <= rules['denominators'].keys()
    # Components of the graph whose vertices are source works and whose edges are case links.
    components = []
    for case in cases:
        papers = {case['later'], *case['earlier']}
        connected = [component for component in components if component & papers]
        components = [component for component in components if component not in connected]
        components.append(papers.union(*connected))
    assert len(components) == 9
    return dict(screened_records=len(screened), retrieval_roster=len(retained),
                worked_eligibility_papers=len(examples), pilot_groups_sharing_papers=len(components))

def check_directions_and_agreement(main, box, paired):
    """Tie the printed direction statements and agreement figures to their recomputed values."""
    plain = main.replace('$', '').replace('{,}', ',')
    resolved = json.loads((ROOT/'results/revision/direction_resolution.json').read_text())
    register = json.loads((ROOT/'data/revision/table_digits.json').read_text())
    assert resolved['rule_sha256'] == register['rule_sha256'] == hashlib.sha256(register['rule'].encode()).hexdigest()
    hill = resolved['periodic_hill']['summary']
    assert hill['contrasts'] == 9 and hill['works'] == 5
    assert hill['by_class'] == {'controls differ': 1, 'resolved concordant': 5, 'resolved opposing': 1, 'unrankable': 1, 'unresolved': 1}
    assert hill['ids_by_class']['resolved opposing'] == ['P25-0.01'] and hill['ids_by_class']['unresolved'] == ['N611']
    assert hill['ids_by_class']['controls differ'] == ['N497'] and hill['ids_by_class']['unrankable'] == ['P25-0.09']
    assert hill['nominal_point_signs'] == dict(both_closer=5, opposite=3, unrankable=1)
    low, high = hill['range_of_changes_in_resolved_concordant_contrasts']
    assert round(low, 2) == 0.06 and round(high) == 2
    assert max(hill['smaller_change_in_each_nominally_opposite_contrast'].values()) <= 0.05 + 1e-12
    rows = {r['id']: r for r in resolved['periodic_hill']['contrasts']}
    krank = rows['N611']
    assert krank['separation']['direction'] == 'unresolved' and krank['reattachment']['direction'] == 'reference dependent'
    assert sorted(v['direction'] for v in krank['reattachment']['by_reference'].values()) == ['closer', 'closer', 'farther']
    digits = {r['id']: r for r in register['hill_population']}
    assert digits['P25-0.01']['baseline_printed'] == ['0.31', '4.26'] and digits['P25-0.01']['alternative_printed'] == ['0.29', '4.18']
    assert digits['P25-0.01']['references']['own wall-resolved LES (H1.0-WR)'] == ['0.22', '4.35']
    assert digits['P25-0.01']['controls']['status'] == 'not all reported' and rows['P25-0.03']['class'] == 'resolved concordant'
    assert digits['N611']['baseline_printed'][0] == '0.2' and digits['N497']['controls']['status'] == 'differ'
    # Two contrasts move the crossings in opposite directions to the printed digits. The class recorded for N497 notes that its
    # two runs were averaged over different intervals. That bears on sampling precision, which neither source reports.
    opposite = sorted(k for k, r in rows.items() if 'separation' in r
                      and {r['separation']['direction'], r['reattachment']['direction']} == {'closer', 'farther'})
    assert opposite == ['N497', 'P25-0.01']
    for phrase in ('Of nine such comparisons, five move both crossings closer, by 0.06H to about 2H',
                   'Two move them in opposite directions, and neither source reports a sampling uncertainty for a crossing',
                   'from 0.31H to 0.29H against 0.22H',
                   'from 4.26H to 4.18H against 4.35H', 'as 0.2, which leaves its 0.05H change unresolved',
                   'about 15 and 19 flow-through times', 'the smaller change is at most 0.05H',
                   'These tables do not establish a trade-off between the two crossings'):
        assert phrase in plain, phrase
    assert not re.search(r'Three nominally bring one closer|favours the learned wall|at each of ten measured', plain)
    sensitivity = resolved['periodic_hill_same_table_sensitivity']['by_class']
    assert 'resolved opposing' not in sensitivity and sum(sensitivity.values()) == 12
    tab = {r['id']: r for r in resolved['other_tabulated']}
    linear = [r for k, r in tab.items() if k.startswith('N364') and k.endswith('linear')]
    blended = [r for k, r in tab.items() if k.startswith('N364') and k.endswith('LUST')]
    assert len(linear) == len(blended) == 4
    assert all(r['class'] == 'resolved opposing' for r in linear) and all(r['class'] == 'resolved concordant' for r in blended)
    rises = [max(v['nominal_change'] for v in r['outputs'].values()) for r in linear]
    assert [round(min(rises), 2), round(max(rises), 2)] == [0.10, 3.65] and 'by 0.10 to 3.65 percentage points' in plain
    assert tab['N626-4-to-5']['class'] == 'unresolved' and tab['MukhaBensow-hex-15-to-30']['class'] == 'resolved farther'
    bump = resolved['bump_station_velocity']
    full, above, below = bump['full_support'], bump['above_0p02'], bump['below_pointwise_crossover']
    assert [round(full['mae_equilibrium'], 3), round(full['mae_learned'], 3)] == [0.010, 0.016]
    assert round(bump['pointwise_equal_error_between'][1], 3) == 0.016 and bump['pointwise_cells'] == [16, 17]
    assert round(below['mean_signed_learned'], 2) == 0.05 and abs(below['mean_signed_equilibrium']) < 0.005
    assert [round(above['mean_signed_equilibrium'], 3), round(above['mean_signed_learned'], 3)] == [0.011, 0.007]
    assert round(bump['reference_shift_that_would_reverse_the_ranking_above_0p02'], 3) == 0.009
    for phrase in ('below y/L\\approx0.016', 'by about 0.011 and 0.007', 'were 0.009 higher', 'by about 0.05',
                   'span 1.5 flow-through times'):
        assert phrase in plain, phrase
    pressure = json.loads((ROOT/'results/revision/paired_error_changes.json').read_text())['fine_DSM_bump']
    assert pressure['pressure_stations_worsening'] == pressure['recovery_pressure']['n'] == 10
    assert [round(pressure['recovery_pressure'][k], 2) for k in ('baseline_mae', 'alternative_mae')] == [0.20, 0.24]
    with (ROOT/'data/revision/measurements/P31_Fig11c_markers.csv').open(newline='') as stream:
        taps = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(stream) if float(r['x_over_L']) > .2]
    gaps = [abs(r['Cp_RLWM']-r['Cp_experiment'])-abs(r['Cp_EQWM']-r['Cp_experiment']) for r in taps]
    assert len(gaps) == 10 and [round(min(gaps), 2), round(max(gaps), 2)] == [0.02, 0.05]
    assert 'on average by 0.20 and 0.24 in C_p' in plain and 'farther at each, by 0.02 to 0.05' in plain
    # Pairings read twice: the second reading received the quantities and locations recorded by the first.
    pairs = json.loads((ROOT/'data/revision/reader_agreement.json').read_text())['pairs']['summary']
    assert pairs['pairs_read_twice'] == 34 and pairs['coarse_agreement_run_pair_or_not']['all'] == [31, 34]
    assert pairs['category_agreement']['other_pairs'] == [12, 24] and pairs['category_agreement']['seeded_different_tests'] == [10, 10]
    assert ("A second automated reading of 34 pairings, given the first reading's quantities and locations, agreed on "
            "31 of 34 same-run judgements and 12 of 24 finer categories") in box
    vocabulary = ['different_tests', 'no_shared_baseline', 'shared_runs_no_treatment_baseline', 'matched_no_common_reference',
                  'matched_no_opposing_rank', 'matched_support_dependent', 'opposing_point_estimates_on_restricted_support',
                  'matched_opposing_same_support']
    assert all(r['adjudication'] in vocabulary and r['decision_tree_reading']['first']['category'] in vocabulary for r in paired)
    counts = Counter(r['adjudication'] for r in paired)
    assert counts['different_tests'] == 55 and counts['matched_opposing_same_support'] == 1
    assert sum(r['decision_tree_reading']['second'] is not None for r in paired) == 34
    memberships = check_memberships(plain, box)
    return dict(hill_classes=hill['by_class'], hill_contrasts_opposite_to_printed_digits=opposite, same_table_other_rows=sensitivity,
                channel_pairs_resolved=8, bump_velocity_reversal_height=bump['pointwise_equal_error_between'],
                pairs_read_twice=34, pair_categories=dict(counts), memberships=memberships)


def check_table_types(comparisons):
    """The type of test printed in Table 2 must follow from the facts recorded for the same comparison."""
    table = (M/'evidence_table.tex').read_text()
    body = table[table.index('\\midrule'):table.index('\\botrule')]
    printed = {}
    for line in body.split('\\\\'):
        keys = [k.strip() for x in arguments(line, 'cite') for k in x.split(',')]
        if keys:
            printed[keys[0]] = arguments(line, 'emph')[0]
    contrasts = {r['contrast_id']: r for r in json.loads((ROOT/'data/revision/wall_change_contrasts.json').read_text())['records']}
    coupled = lambda c: c['feedback'].startswith('coupled')
    fixed = lambda c, *names: all(c['factors'][n] == 'fixed' for n in names)
    fits = {
        'prescribed input': lambda c: c['feedback'] == 'prescribed input' and c['derived']['tier'] == 'none',
        'wall model changed': lambda c: coupled(c) and c['variant_type'] == 'different model' and fixed(c, 'grid', 'outer_closure')
                                        and c['derived']['tier'] in ('strict', 'upper'),
        'wall condition changed': lambda c: coupled(c) and c['variant_type'] == 'same model, different imposition' and c['derived']['tier'] == 'broad',
        'grid changed': lambda c: coupled(c) and c['factors']['grid'] == 'varied' and c['derived']['tier'] == 'none',
        'complete systems': lambda c: coupled(c) and c['variant_type'] == 'different model' and c['factors']['grid'] == 'varied'
                                      and c['derived']['tier'] == 'none',
        'within one outer closure': lambda c: c['variant_type'] == 'different model' and fixed(c, 'grid', 'outer_closure'),
    }
    needs = {'Prescribed input': {'prescribed input'}, 'Coupled, wall model changed': {'wall model changed'},
             'Coupled, grid changed': {'grid changed'}, 'Coupled, outer closure changed': set(),
             'Complete systems, then coupled, wall condition changed': {'complete systems', 'wall condition changed'}}
    for row in comparisons['rows']:
        label = row['type_of_test']
        assert printed[row['reference_key']] == label, (row['reference_key'], printed[row['reference_key']])
        roles = set()
        for link in row['recorded_contrasts']:
            contrast = contrasts[link['contrast_id']]
            assert contrast['work_counted'] and fits[link['role']](contrast), link
            roles.add(link['role'])
        assert needs[label] <= roles, (row['reference_key'], roles)
        if label == 'Coupled, outer closure changed':
            assert 'Outer closure' in row['changes'] and row['recorded_contrasts_note']
        if any(contrasts[l['contrast_id']]['derived']['tier'] == 'upper' for l in row['recorded_contrasts']):
            assert row['recorded_contrasts_note']
    assert len(printed) == len(comparisons['rows']) == 8
    return Counter(row['type_of_test'] for row in comparisons['rows'])


SMALL = ('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen '
         'eighteen nineteen').split()
TENS = dict(zip(range(20, 100, 10), 'twenty thirty forty fifty sixty seventy eighty ninety'.split()))


def spell(n, capital=False):
    """Number word as printed at the start of a sentence or below twenty; whole tens are spelled, other numbers stay digits."""
    word = SMALL[n] if n < 20 else TENS[n] if n in TENS else str(n)
    return word.capitalize() if capital else word


def check_memberships(plain, box):
    """Tie every count of reports and tests printed in the paper to the derived memberships and the agreement record.

    Each printed sentence is formatted here from the derived values, so a count, its value without boundary cases or its
    value within the primary scope cannot be changed or removed in the text without failing this check."""
    derived = json.loads((ROOT/'results/revision/derived_memberships.json').read_text())
    agreement = json.loads((ROOT/'data/revision/agreement_v2.json').read_text())
    recomputed = json.loads((ROOT/'results/revision/agreement_check.json').read_text())
    records = json.loads((ROOT/'data/revision/source_dispositions.json').read_text())['records']
    regime = json.loads((ROOT/'data/revision/regime_facts.json').read_text())
    status = Counter(r['eligibility_status'] for r in records)
    population, decisions, stats = derived['population'], agreement['decisions'], agreement['statistics']
    eligible = status['documented eligible design']
    assert population['works'] == len(records) == 115 and population['eligible_works'] == eligible
    kinds = population['scope_boundary_by_kind']
    boundary_ids = population['scope_boundary_works']
    assert len(boundary_ids) == sum(kinds.values())
    order = ('sublayer-resolving near-wall method', 'estimator not presented as a wall model',
             'eligibility disputed between the readings on a rule ambiguity')
    assert set(kinds) <= set(order)
    narrow = population['eligible_works_without_scope_boundary']
    assert narrow == eligible - len(boundary_ids)
    eligible_ids = {r['study_id'] for r in records if r['eligibility_status'] == 'documented eligible design'}
    assert set(boundary_ids) <= eligible_ids

    # Sample: a random 30 of the 79 works that were not read twice on 19 November, and the two pools.
    sample = agreement['sample']
    assert len(sample['fresh_sample_frame']) == 79 and set(sample['fresh_random_sample']) <= set(sample['fresh_sample_frame'])
    assert len(sample['fresh_random_sample']) == 30 and len(sample['all_works_read_twice']) == 74
    assert agreement['protocol']['rule_file_fixed_at'] < agreement['protocol']['settlement_plan_fixed_at']
    work = {w['study_id']: w for w in agreement['per_work']}
    same_disposition = lambda ids: sum(work[i]['first']['disposition'] == work[i]['second']['disposition'] for i in ids)
    agree_sample, agree_all = same_disposition(sample['fresh_random_sample']), same_disposition(sample['all_works_read_twice'])

    # Matched wall-treatment contrast. Only tiers that met the criteria fixed in advance are printed.
    tiers = derived['matched_wall_treatment_change']['tiers']
    broad, upper = tiers['broad'], tiers['upper']
    scope = population['primary_scope']
    assert decisions['broad']['quotable'] and decisions['upper']['quotable'] and not decisions['strict']['quotable']
    assert all(recomputed[k]['quotable'] == decisions[k]['quotable'] for k in recomputed if 'quotable' in recomputed[k])
    fresh = stats['fresh_random_sample']
    assert [round(fresh['broad']['kappa'], 2), round(fresh['broad']['kappa_bootstrap_95'][0], 2)] == [0.87, 0.67]
    strict = fresh['strict']
    assert abs(strict['members_second'] - strict['members_first']) > max(1, 0.15 * strict['members_first'])
    disputed = sorted(i for i in sample['fresh_random_sample'] if 'broad' in work[i]['disagreements'])
    boundary = {b['study_id']: b for b in agreement['settlement']['scope_boundary']}
    assert len(disputed) == 2 and all(boundary[i]['kind'] == 'sublayer-resolving near-wall method' for i in disputed)
    settled = {(i['study_id'], i['question']): i for i in agreement['settlement']['items']}
    assert all(settled[i, 'scope']['attribution'] == 'rule ambiguity' for i in disputed)
    assert round(fresh['system_benchmark']['kappa'], 2) == 0.15 and not decisions['system_benchmark']['quotable']

    # Constitutive constraint and transfer.
    constitutive, pool = derived['constitutive_constraint'], stats['constitutive_pool']['constitutive']
    assert constitutive['works'] == len(constitutive['members']) and decisions['constitutive_constraint']['quotable']
    has_row = stats['transfer_pool']['has_transfer']
    assert [round(pool['kappa'], 2), round(has_row['kappa'], 2)] == [0.67, 0.86]
    assert [round(pool['kappa_bootstrap_95'][0], 2), round(has_row['kappa_bootstrap_95'][0], 2)] == [0.44, 0.61]
    both_readings = {i for i in sample['constitutive_pool'] if work[i]['first']['constitutive'] and work[i]['second']['constitutive']}
    members_outside_boundary = set(constitutive['members']) - set(boundary_ids)
    assert members_outside_boundary <= both_readings, 'a member outside the boundary cases was found by one reading only'
    assert len(members_outside_boundary) == constitutive['works_without_scope_boundary']
    transfer = derived['transfer']
    whole, without, within = transfer['all_counted_works'], transfer['without_scope_boundary'], transfer['in_primary_scope']
    assert decisions['transfer']['quotable']
    rows = [r for r in json.loads((ROOT/'data/revision/transfer_exposure.json').read_text())['records'] if r['work_counted']]
    assert Counter(r['status'] for r in rows) == whole['tests'] and len(rows) == whole['total_tests']
    assert all(r['frozen_external'] or r['holdout_statement'] for r in rows if r['status'] == 'qualified')
    by_work = Counter(r['study_id'] for r in rows if r['status'] == 'qualified')
    study = next(r for r in records if r['study_id'] == by_work.most_common(1)[0][0])
    bib = (M/'references.bib').read_text()
    entry = bib[bib.index('LozanoDuranBae2023,'):].split('\n@')[0]
    assert study['doi'] in entry
    qualified_outside = transfer['qualified_tests_outside_primary_scope']
    assert [axes for _, axes in qualified_outside] == ['surface'], qualified_outside
    assert whole['tests']['qualified'] - within['tests']['qualified'] == len(qualified_outside)

    # Regime of the counted tests and first-cell spacing of the coupled designs (fourth reading).
    assert regime['rule']['fixed_at'] < regime['clarification']['written_at']
    assert scope['recorded_tests'] == regime['items'] and scope['recorded_tests_outside'] == len(regime['outside_primary_scope'])
    wholly_outside = scope['eligible_works_wholly_outside']
    assert scope['eligible_works_inside'] == eligible - len(wholly_outside)
    axes = set()
    for r in records:
        if r['study_id'] in wholly_outside:
            assert all(t['regime']['primary_scope'] == 'outside' for t in r['tests'] if {'prescribed_input', 'coupled_wmles', 'rans_comparison', 'thermal'} & set(t['groups']))
            axes |= {a for t in r['tests'] for a in t['regime']['axes_outside']}
    assert axes == {'surface', 'compressibility', 'thermal_coupling'}, axes
    added = agreement['fourth_reading']['scope_boundary_added']
    assert set(boundary_ids) == set(boundary) | {a['study_id'] for a in added} and not set(boundary) & {a['study_id'] for a in added}
    assert len(added) == 1 and all(a['kind'] == order[1] and a['quotes'] for a in added), 'reword the sentence on boundary cases added by the fourth reading'
    assert agreement['fourth_reading']['quotations']['not_found'] == 0
    first_cell = population['first_cell_class_of_eligible_works']
    assert sum(first_cell.values()) == eligible and first_cell['every design reaches the sublayer'] == kinds[order[0]]

    q, pe, un = 'qualified', 'partly exposed', 'selection unresolved'
    more = upper['works'] - broad['works']
    more_restricted = {upper[k] - broad[k] for k in ('works_without_scope_boundary', 'works_in_primary_scope')}
    assert len(more_restricted) == 1, 'the two restricted counts of reports with an unreported control differ: print both'
    most = by_work.most_common(1)[0][1]
    assert whole['works'][q] - within['works'][q] == len(qualified_outside) == 1, 'reword the sentence on the qualified test outside the primary scope'
    ordinal = {1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth', 6: 'sixth'}
    assert 'at or below 0.3' in regime['rule']['text'], 'the Mach threshold printed in Box 1 is the threshold of the rule'
    main_phrases = (
        f"Of {eligible} eligible reports, {broad['works']} contain two coupled calculations that differ only in the wall treatment or its implementation",
        f"for a hydrodynamic quantity ({broad['works_without_scope_boundary']} of {narrow} without boundary cases; "
        f"{broad['works_in_primary_scope']} of {scope['eligible_works_inside']} within our primary scope)",
        f"{spell(more, True)} more, {spell(more_restricted.pop())} on either restricted basis, leave one of those controls unreported",
        f"{spell(constitutive['works'], True)} reports test an assumption shared by a class of wall laws on reference data alone "
        f"({constitutive['works_without_scope_boundary']} without boundary cases, {constitutive['works_in_primary_scope']} within the primary scope)",
        f"{whole['total_works']} reports test a fitted treatment at {whole['total_tests']} conditions outside the data used to fit it",
        f"{spell(whole['tests'][q], True)} tests in {spell(whole['works'][q])} reports state that the target was withheld from training and model "
        "selection or apply unchanged coefficients published earlier by other authors",
        f"{spell(most, True)} of the {spell(whole['tests'][q])} come from one study",
        f"and {spell(len(qualified_outside))}, a rough-wall channel, lies outside our primary scope",
        f"{spell(whole['tests'][pe], True)} compare variants of the treatment at the target or select with it, and {whole['tests'][un]} remain unresolved",
        f"Without boundary cases the counts are {without['total_tests']} conditions in {without['total_works']} reports "
        f"({without['tests'][q]}, {without['tests'][pe]} and {without['tests'][un]}); within the primary scope, "
        f"{within['total_tests']} in {within['total_works']} ({within['tests'][q]}, {within['tests'][pe]} and {within['tests'][un]})")
    for phrase in main_phrases:
        assert phrase in plain, phrase
    assert 'outside those that determined it' not in plain, 'the transfer sentence must use the fitting-set definition of the rule'
    box_phrases = (
        'All readings were automated', 'covered a random 30 of the 79 reports not used to write the rules',
        'A third, which saw both, settled each disagreement against the source',
        f"After settlement {eligible} reports are eligible, {spell(status['contested'])} contested and {spell(status['excluded'])} excluded",
        f"The first two readings agreed on eligibility for {agree_sample} of the {len(sample['fresh_random_sample'])} sampled reports and "
        f"{agree_all} of the {len(sample['all_works_read_twice'])} read twice",
        r"Cohen's $\kappa=0.87$ (lower 95\,\% bound 0.67)", 'Clarifications written after that test, before the third reading',
        f"{spell(len(boundary_ids), True)} eligible reports are boundary cases: {spell(kinds[order[0]])} use those methods, {spell(kinds[order[1]])} test "
        f"stress estimators never presented as wall models and {spell(kinds[order[2]])} had disputed eligibility",
        'A fourth reading, done once, completed the record of first-cell spacing for every coupled design and recorded the flow regime of every counted test',
        f"It added the {ordinal[kinds[order[1]]]} estimator; {spell(first_cell['not stated'])} reports state no first-cell distance in wall units and "
        f"{spell(len(wholly_outside))} test only flows outside the primary scope",
        'Counts are given for the collection, without boundary cases and within the primary scope',
        r'$\kappa$ was 0.67 and 0.86 (lower bounds 0.44 and 0.61)',
        f"The readings found {pool['members_first']} and {pool['members_second']} constitutive members; both found the "
        f"{constitutive['works_without_scope_boundary']} that are not boundary cases",
        r'did not reproduce ($\kappa=0.15$)', 'We quote neither',
        'Our primary scope is turbulent flow of a single-phase Newtonian fluid with constant properties and no buoyancy over smooth walls at '
        'Mach numbers up to 0.3')
    for phrase in box_phrases:
        assert phrase in box, phrase
    # Counts that failed the criteria, and the figures they replaced, stay out of the paper.
    text = plain + box
    assert not re.search(r'\b50 of 108\b|\b47 of 97\b|\b45 of 104\b|\b50 contain\b|0\.89--0\.94|reading of 36 reports|for which we quote no counts', text)
    assert not re.search(r'\b(?:three|3) (?:qualified|independent) (?:transfer|test)', text, re.I)
    return dict(eligible_reports=eligible, boundary_cases=kinds,
                matched_wall_treatment_contrast={k: dict(collection=tiers[k]['works'], without_boundary_cases=tiers[k]['works_without_scope_boundary'],
                                                         within_primary_scope=tiers[k]['works_in_primary_scope']) for k in ('strict', 'broad', 'upper')},
                denominators=dict(collection=eligible, without_boundary_cases=narrow, within_primary_scope=scope['eligible_works_inside']),
                constitutive_reports=dict(collection=constitutive['works'], without_boundary_cases=constitutive['works_without_scope_boundary'],
                                          within_primary_scope=constitutive['works_in_primary_scope']),
                transfer_tests=dict(collection=whole['tests'], without_boundary_cases=without['tests'], within_primary_scope=within['tests']),
                eligibility_agreement=dict(sample=[agree_sample, 30], read_twice=[agree_all, 74]),
                eligible_reports_wholly_outside_primary_scope=wholly_outside, first_cell_class=first_cell,
                printed_sentences_checked=len(main_phrases) + len(box_phrases),
                quotable={k: v['quotable'] for k, v in decisions.items()})


def main_check():
    support=json.loads((ROOT/'data/revision/claim_support.json').read_text())
    cited={k.strip() for x in arguments(alltext,'cite') for k in x.split(',')}
    covered={r['reference_key'] for r in support}
    assert cited<=covered,('unsupported citations',sorted(cited-covered))
    bib=(M/'references.bib').read_text()
    bibkeys=re.findall(r'@\w+\{([^,]+),',bib)
    assert len(bibkeys)==len(set(bibkeys)),'duplicate bibliography keys'
    assert cited<=set(bibkeys)
    caps=[words(x) for s in parts for x in arguments(s,'caption')]
    assert len(caps)==7 and max(caps)<150,caps
    abstract=arguments(main,'abstract')[0]
    assert words(abstract)<=150 and not arguments(abstract,'cite')
    assert main.count('\\includegraphics')==4
    assert alltext.count('\\begin{table*}')==3
    assert '\\input{numbers}' not in main
    assert not re.search(r'\\n(?:Claims|Obs|Mixed|Exposed|Held|Adv)\b',alltext)
    # The superseded counts belong to the correction record. The paper reports selected cases.
    status = json.loads((ROOT/'data/revision/STATUS.json').read_text())
    assert 'population prevalence of transfer or validation deficit' in status['withdrawn_claims']
    assert '9-of-18 quantity-only contrast' in status['withdrawn_claims']
    assert not re.search(r'we withdrew estimates|archived literature counts|'
                         r'82 study treatments|eligibility decisions for the other 33', alltext, re.I)
    assert 'retrospective' in abstract and 'prospective' in abstract

    dup=json.loads((ROOT/'data/revision/dupuy_table5.json').read_text())
    # Values independently transcribed from the visually checked published Table 5.
    assert dup['baseline_magnitude']==0.806 and dup['baseline_streamwise_component']==0.686
    assert dup['magnitude']==[.687,.217,.120,.067,.066]
    assert dup['streamwise_component']==[.585,.311,.302,.308,.367]
    comparisons=json.loads((ROOT/'data/revision/comparison_map.json').read_text())
    plotted_map=json.loads((ROOT/'results/figures/fig2_values.json').read_text())
    by_id={r['claim_id']:r for r in support}
    assert len(comparisons['rows'])==len({r['reference_key'] for r in comparisons['rows']})==8
    assert plotted_map['rows']==comparisons['rows']
    check_figure2(comparisons, plotted_map, by_id)
    step=next(r['figure_example'] for r in comparisons['rows'] if r['reference_key']=='Dupuy2023graph')
    positions={t['treatment']:t['x_over_hs_approx'] for t in step['crossings']}
    ordered=[positions[k] for k in ('Log law','Graph, N = 4','Reference')]
    step_sentence=next(s for s in re.split(r'(?<=\.)\s+',abstract) if 'step heights' in s)
    assert [float(x) for x in re.findall(r'\b\d+\.\d+\b',step_sentence)]==ordered
    shortfalls=[round(ordered[-1]-v,1) for v in ordered[:2]]
    assert f'shortfall from about {shortfalls[0]} to {shortfalls[1]} step heights' in main.replace('$','')
    for row in comparisons['rows']:
        assert row['reference_key'] in cited
        assert row['source_location'] and row['selected_comparison']
        assert row['support'] and all(by_id[k]['reference_key']==row['reference_key'] for k in row['support'])
        assert set(row['changes'])<=set(comparisons['change_columns'])
        assert set(row['quantities'])<=set(comparisons['quantity_columns'])
    plotted_errors=json.loads((ROOT/'results/figures/fig3_values.json').read_text())
    for source_key,baseline_key,plotted_key in [('magnitude','baseline_magnitude','magnitude_ratio'),
                                              ('streamwise_component','baseline_streamwise_component','streamwise_ratio')]:
        assert len(dup[source_key])==len(plotted_errors[plotted_key])==5
        assert all(math.isclose(a/dup[baseline_key],b,rel_tol=1e-12)
                   for a,b in zip(dup[source_key],plotted_errors[plotted_key]))
    outer=json.loads((ROOT/'data/revision/outer_input_error.json').read_text())
    assert plotted_errors['outer_input_comparison']==outer
    assert outer['internal_error']['BFWM']==dict(relation='less than',value=.5)
    assert outer['internal_error']['EQWM']==dict(relation='approximately',value=2.)
    assert outer['total_error']['reported_range_percent']==[5.,15.]
    station_data = outer['station_readings']
    assert station_data['re_x'] == [600000, 800000, 1000000, 1200000]
    station_series = {(s['outer_closure'], s['wall_model']): s for s in station_data['series']}
    closures = ['Exact for the mean', 'Dynamic Smagorinsky', 'Vreman']
    assert len(station_data['series']) == 6
    assert set(station_series) == {(c, m) for c in closures for m in ('EQWM', 'BFWM')}
    for (closure, _), series in station_series.items():
        assert series['source_panel'] == ('c' if closure == 'Exact for the mean' else 'd')
        cal = station_data['calibration'][series['source_panel']]
        y1, y10 = cal['y_at_1_percent_pt'], cal['y_at_10_percent_pt']
        assert len(series['y_pt']) == len(series['error_percent_approx']) == len(cal['station_x_pt']) == 4
        percent = [10**((y1-y)/(y1-y10)) for y in series['y_pt']]
        assert [float(f'{v:.2g}') for v in percent] == series['error_percent_approx']
    assert station_series['Dynamic Smagorinsky', 'EQWM']['error_percent_approx'][2] == 19
    cases=json.loads((ROOT/'data/checklist_cases.json').read_text())['cases']
    keys=['same_cause','same_observable_class','same_factor']
    agreement=[sum(c['agreement'][k] for c in cases) for k in keys]
    agreement.append(sum(all(c['agreement'][k] for k in keys) for c in cases))
    assert len(cases)==13 and agreement==[8,10,7,3]
    assert sum(c['group']=='P' for c in cases)==4
    plotted_cases=json.loads((ROOT/'results/figures/fig4_values.json').read_text())
    assert list(plotted_cases['agreement'].values())==agreement
    assert plotted_cases['case_order']==[dict(number=i+1,case=c['case'],agreement=c['agreement']) for i,c in enumerate(cases)]
    counts_by_degree=check_checklist_patterns(cases,keys,plotted_cases)
    assert all(c['records'][p]['step5_from_the_item_record']=='unknown' for c in cases for p in ['A','B'])
    exclusions=json.loads((ROOT/'data/revision/eligibility_audit.json').read_text())
    manifest=json.loads((ROOT/'data/revision/historical_source_manifest.json').read_text())
    assert len(exclusions)==len({x['study_id'] for x in exclusions})==33
    assert len(manifest)==115 and sum(x['historical_cohort'] for x in manifest)==82
    assert {x['study_id'] for x in exclusions}=={x['study_id'] for x in manifest if not x['historical_cohort']}

    pdf=M/'main.pdf'
    info=subprocess.check_output(['pdfinfo',str(pdf)],text=True)
    pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))
    assert 0<pages<=15,pages
    assert not any(M.glob('supplement*.pdf')) and not any(M.glob('appendix*.pdf'))
    text=subprocess.check_output(['pdftotext',str(pdf),'-'],text=True)
    assert '??' not in text,'unresolved PDF reference'
    compiled_keys=re.findall(r'\\bibitem\{([^}]+)\}',(M/'main.bbl').read_text())
    assert len(compiled_keys)==len(cited) and set(compiled_keys)==cited,'compiled bibliography differs from citations'
    compact=re.sub(r'\s+',' ',text)
    # The only permitted use is the genuine title of the cited Bae paper.
    cleaned=re.sub(r'multi-?\s*agent reinforcement learning','reinforcement learning',compact,flags=re.I)
    banned=r'\b(?:AI|LLM|GPT|Claude|Codex|Anthropic|OpenAI|agents?|reader|recalled|card)\b|certainly holding|Jianou|Jiang|jianou\.jiang'
    hits=re.findall(banned,cleaned,re.I)
    assert not hits,hits
    assert 'Authors: to be decided' in compact
    assert 'no competing interests' in compact and 'no specific funding' in compact
    log=(M/'main.log').read_text(errors='replace')
    assert 'Output written on main.pdf' in log,'LaTeX did not finish writing the PDF'
    assert not re.search(r'^!|Fatal error occurred|Emergency stop',log,re.M),'LaTeX error'
    assert not re.search(r'undefined references|Citation .* undefined|Overfull \\[hv]box',log)
    assert all(title in compact for title in ('Plane channel', 'Flat-plate boundary layers',
               'Gaussian speed bump', 'Step and diffuser', 'Signed error in mean wall stress',
               'First-cell mean velocity', 'Recirculation on the inclined diffuser wall')), 'outdated Figure 2 in PDF'
    assert all(s in compact for s in ('Backward-facing step with a graph wall model', 'Streamwise component',
               'Internal error', 'Total error', 'Two comparisons of coupled wall-stress predictions')), 'outdated Figure 3 in PDF'
    assert all(t in compact for t in ('Agreement by choice', 'Cases by combination of matches', 'Case IDs')), 'outdated Figure 4 in PDF'
    assert all(c['case'] in compact for c in cases), 'missing Figure 4 case identifier'
    selection = check_evidence_selection(comparisons, cases)
    table_types = check_table_types(comparisons)
    heading_count=check_panel_style(comparisons)
    figure_layouts={name:json.loads((ROOT/f'results/figures/{name}_layout.json').read_text())['passed']
                    for name in ('fig1_loop','fig2_record','fig3_contrast','fig4_checklist')}
    assert all(figure_layouts.values())
    report={'status':'PASS','edition':'critical review; aggregate claims withdrawn',
            'pdf_pages':pages,'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
            'citations_with_support_record':len(cited),'caption_word_counts':caps,
            'abstract_words':words(arguments(main,'abstract')[0]),
            'figures':4,'tables':3,'eligibility_records_checked':33,
            'dupuy_N4_normalised_errors':[.067/.806,.308/.686],
            'retrospective_agreement':agreement,
            'checklist_cases_by_number_of_matching_choices':dict(enumerate(counts_by_degree)),
            'panel_headings_matching_figure_1':heading_count,
            'comparison_map_sources':len(comparisons['rows']), 'study_selection':selection,
            'table_2_types_of_test':dict(table_types),
            'figure_layouts':figure_layouts,
            'circulation_text_scan':'PASS',
            'scientific_limit':'Pass checks consistency and specified support. It does not certify an exhaustive corpus or predictive checklist validity.'}
    audited=json.loads((ROOT/'data/revision/source_dispositions.json').read_text())['records']
    paired=json.loads((ROOT/'data/revision/paired_readings.json').read_text())['records']
    eligible=json.loads((ROOT/'results/revision/eligible_units.json').read_text())
    assert sum(eligible['disposition'].values())==len(audited)==115
    assert len(paired)==79 and sum(r['original_nomination'] for r in paired)==10
    report['archived_source_dispositions']=len(audited)
    report['historical_pairs_reassessed']=len(paired)
    report['source_located_design_series']=sum(len(r['tests']) for r in audited)
    report['edition']='Review with finite-sample source reassessment and edition-specific comparisons'
    report['direction_and_agreement_checks']=check_directions_and_agreement(main, (M/'methods_box.tex').read_text(), paired)
    (ROOT/'results/revision/current_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main_check()
