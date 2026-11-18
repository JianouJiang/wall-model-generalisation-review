#!/usr/bin/env python3
"""Check the current critical review without validating superseded census claims."""
import hashlib
import json
import math
import re
import subprocess
from itertools import product
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
    pairs = example('Mukha2024preprint')['measurements']
    assert [(p['mesh'], p['coupled'], p['offline_mean']) for p in pairs] == [
        ('M1', .71, .06), ('M2', .76, .20), ('M3', -.54, -1.07)]
    sweep = example('Hayat2024preprint')
    assert sweep['sweep_degrees'] == [0, 35]
    assert [m['signs'] for m in sweep['measurements']] == [[1, -1], [1, -1], [-1, -1]]
    closures = example('LozanoDuranBae2023')['measurements']
    assert [(m['outer_closure'], m['stress_error']) for m in closures] == [
        ('Exact for the mean', 'Internal'), ('Dynamic Smagorinsky', 'Total'), ('Vreman', 'Total')]
    outer, wall = example('Zhou2024preprint'), example('Agrawal2024')
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
    assert words(arguments(main,'abstract')[0])<=150
    assert main.count('\\includegraphics')==4
    assert alltext.count('\\begin{table*}')==3
    assert '\\input{numbers}' not in main
    assert not re.search(r'\\n(?:Claims|Obs|Mixed|Exposed|Held|Adv)\b',alltext)
    assert 'aggregate transfer and quantity-only estimates are withdrawn' in main
    assert 'does not establish predictive' not in main or 'retrospective' in main
    assert 'does not' in main and 'no estimate of the prevalence' in main

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
               'Prescribed mean stress, baseline mesh', 'Recirculation on the inclined diffuser wall')), 'outdated Figure 2 in PDF'
    assert all(s in compact for s in ('Backward-facing step with a graph wall model', 'Streamwise component',
               'Internal error', 'Total error', 'Two comparisons of coupled wall-stress predictions')), 'outdated Figure 3 in PDF'
    assert all(t in compact for t in ('Agreement by choice', 'Cases by combination of matches', 'Case IDs')), 'outdated Figure 4 in PDF'
    assert all(c['case'] in compact for c in cases), 'missing Figure 4 case identifier'
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
            'comparison_map_sources':len(comparisons['rows']),
            'figure_layouts':figure_layouts,
            'circulation_text_scan':'PASS',
            'scientific_limit':'Pass checks consistency and specified support. It does not certify an exhaustive corpus or predictive checklist validity.'}
    (ROOT/'results/revision/current_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main_check()
