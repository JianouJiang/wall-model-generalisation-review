#!/usr/bin/env python3
"""Check the current critical review without validating superseded census claims."""
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

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
    assert 'not confidence intervals' in main
    cases=json.loads((ROOT/'data/checklist_cases.json').read_text())['cases']
    keys=['same_cause','same_observable_class','same_factor']
    agreement=[sum(c['agreement'][k] for c in cases) for k in keys]
    agreement.append(sum(all(c['agreement'][k] for k in keys) for c in cases))
    assert len(cases)==13 and agreement==[8,10,7,3]
    plotted_cases=json.loads((ROOT/'results/figures/fig4_values.json').read_text())
    assert list(plotted_cases['agreement'].values())==agreement
    assert plotted_cases['case_order']==[dict(number=i+1,case=c['case'],agreement=c['agreement']) for i,c in enumerate(cases)]
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
    assert 'Internal and total error' in compact,'outdated accuracy figure in PDF'
    assert 'Agreement in each case' in compact,'outdated checklist figure in PDF'
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
            'comparison_map_sources':len(comparisons['rows']),
            'figure_layouts':figure_layouts,
            'circulation_text_scan':'PASS',
            'scientific_limit':'Pass checks consistency and specified support. It does not certify an exhaustive corpus or predictive checklist validity.'}
    (ROOT/'results/revision/current_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main_check()
