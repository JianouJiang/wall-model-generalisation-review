#!/usr/bin/env python3
"""Research figure rendering from the accompanying public data."""
import csv
import json
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from matplotlib.patches import Rectangle, Polygon
import matplotlib.pyplot as plt
from style import *

def main():
    ret = json.load(open(os.path.join(DATA, 'later_tests.json')))
    cas = json.load(open(os.path.join(DATA, 'checklist_cases.json')))
    corpus = {r['study_id']: r for r in csv.DictReader(open(os.path.join(DATA, 'studies.csv')))}
    printed = printed_refs()

    def label(sid):
        ref = printed[corpus[sid]['bib_key']]
        return f"{ref['surname']} {ref['year']} [{ref['n']}]"
    plotted = dict(a={}, b={})
    H = 152.0
    fig = plt.figure(figsize=(W * MM, H * MM))
    fy = lambda mm: 1 - mm / H
    fx = lambda mm: mm / W
    letter(fig, 0.012, fy(4.5), 'a', 'Later coupled tests, matched to the earlier paper by type of flow and class of quantity')
    groups = (('later_study_is_new_same_treatment', 'same treatment'), ('later_study_is_new_modified_successor', 'modified successor'))
    GX = (50.0, 106.0)
    GW = 44.0
    row_labels = ('earlier: no match', 'earlier: favourable', 'earlier: adverse or unclear')
    for (gi, (key, head)) in enumerate(groups):
        t = ret['totals'][key]
        ct = t['crosstab']
        other = {r: ct['adverse or both'][r] + ct['matched, no resolved result'][r] + ct['undetermined'][r] for r in ct['unknown']}
        ax = fig.add_axes([fx(GX[gi]), fy(39), fx(GW), fy(15) - fy(39)])
        rows = ((row_labels[0], ct['unknown']), (row_labels[1], ct['favourable']), (row_labels[2], other))
        for (i, (lab, v)) in enumerate(rows):
            y = 2 - i
            x = 0
            for (k, col) in (('adverse', RED), ('favourable', BLUE), ('none', G2), ('undetermined', G3)):
                w = v[k]
                if w:
                    ax.add_patch(Rectangle((x, y - 0.32), w, 0.64, fc=col, ec=G1 if col == G3 else 'white', lw=0.6))
                if w >= 2:
                    ax.text(x + w / 2, y, str(w), ha='center', va='center', fontsize=FS, color='white' if col in (RED, BLUE) else INK)
                x += w
            if gi == 0:
                ax.text(-0.6, y, lab, ha='right', va='center', fontsize=FS)
            plotted['a'][f'{head} | {lab}'] = dict(v, total=x)
        ax.set_xlim(0, 23)
        ax.set_ylim(-0.5, 2.5)
        ax.set_yticks([])
        ax.set_xticks([0, 10, 20])
        for sp in ('top', 'right', 'left'):
            ax.spines[sp].set_visible(False)
        ax.set_title(f"{head} ({t['later_studies']} studies)", fontsize=FS, color=MUTE, loc='left', pad=3)
    yl = fy(48)
    fig.text(fx(GX[0]), yl, 'later result:', fontsize=FS, va='center', color=MUTE)
    lx = GX[0] + 20.0
    for (col, lab) in ((RED, 'adverse'), (BLUE, 'favourable'), (G2, 'neither'), (G3, 'uncertain')):
        fig.patches.append(Rectangle((fx(lx), yl - 1.4 / H), fx(2.8), 2.8 / H, transform=fig.transFigure, fc=col, ec=G1 if col == G3 else 'none', lw=0.6))
        fig.text(fx(lx + 3.8), yl, lab, fontsize=FS, va='center')
        lx += 3.8 + 1.6 * len(lab) + 3.5
    letter(fig, 0.012, fy(58), 'b', f"The checklist applied to the earlier work, then compared with {len(cas['cases'])} later papers")
    cases = cas['cases']
    for c in cases:
        assert c['records']['A']['adverse_rows_n'] == c['records']['B']['adverse_rows_n'], c['case']
    (xs, x) = ({}, 0.0)
    for c in cases:
        if c['group'] == 'P' and (not any((k['group'] == 'P' for k in cases[:cases.index(c)]))):
            x += 0.8
        xs[c['case']] = x
        x += 1.0
    dx = fig.add_axes([fx(46), fy(133), fx(100), fy(87) - fy(133)])
    ROWS = [('step 5 (pass 1, 2)', 9, INK), ('passes agree: cause', 8, INK), ('passes agree: quantity', 7, INK), ('passes agree: factor', 6, INK), ('pass 1', 5, INK), ('pass 2', 4, INK), ('later adverse results', 3, INK), ('pass 1', 2, MUTE), ('pass 2', 1, MUTE)]
    for (lab, yy, col) in ROWS:
        dx.text(-0.7, yy, lab, ha='right', va='center', fontsize=FS, color=col)
    dx.text(-2.15, 4.5, 'proposed test run', ha='right', va='center', fontsize=FS, color=INK)
    dx.text(-2.15, 1.5, 'of these, on the\nproposed cause\nand quantity', ha='right', va='center', fontsize=FS, color=MUTE, linespacing=1.0)
    for (y0, y1) in ((8.5, 9.5), (6.5, 7.5), (3.5, 5.5), (0.5, 1.5)):
        dx.add_patch(Rectangle((-0.55, y0), x + 0.1, y1 - y0, fc=BAND, ec='none', zorder=0))

    def result_box(xc, yc, ran, res):
        hw = 0.24
        if ran == 'not run':
            dx.add_patch(Rectangle((xc - hw, yc - hw), 2 * hw, 2 * hw, fc='white', ec=G1, lw=0.6, zorder=3))
            return
        if res == 'mixed':
            dx.add_patch(Polygon([(xc - hw, yc - hw), (xc - hw, yc + hw), (xc + hw, yc + hw)], fc=BLUE, ec='none', zorder=3))
            dx.add_patch(Polygon([(xc - hw, yc - hw), (xc + hw, yc - hw), (xc + hw, yc + hw)], fc=RED, ec='none', zorder=3))
        else:
            dx.add_patch(Rectangle((xc - hw, yc - hw), 2 * hw, 2 * hw, fc={'favourable': BLUE, 'adverse': RED}.get(res, G2), ec='none', zorder=3))
        if ran == 'in full':
            dx.add_patch(Rectangle((xc - hw - 0.08, yc - hw - 0.08), 2 * hw + 0.16, 2 * hw + 0.16, fc='none', ec=INK, lw=0.8, zorder=4))

    def bound(d):
        return str(d['confirmed']) if d['confirmed'] == d['possible'] else f"{d['confirmed']}–{d['possible']}"
    drawn = set()
    for c in cases:
        xc = xs[c['case']]
        dx.text(xc - 0.1, 9.75, label(c['later']), ha='left', va='bottom', rotation=50, rotation_mode='anchor', fontsize=FS)
        rec = dict(later=c['later'], group=c['group'], kind=c['kind'])
        for (r, off) in (('A', -0.17), ('B', 0.17)):
            a5 = c['records'][r]['step5_from_the_item_record']
            dx.add_patch(Rectangle((xc + off - 0.13, 9 - 0.16), 0.26, 0.32, fc=BLUE if a5 == 'yes' else 'white', ec=BLUE if a5 == 'yes' else INK, lw=0.6, zorder=3))
            rec[f'step5_{r}'] = a5
        for (key, yy) in (('same_cause', 8), ('same_observable_class', 7), ('same_factor', 6)):
            same = c['agreement'][key]
            dx.plot(xc, yy, 'o', ms=5 if same else 3.2, mfc=INK if same else 'white', mec=INK if same else G1, mew=0.6, zorder=3)
            rec[key] = same
        for (r, yy) in (('A', 5), ('B', 4)):
            R = c['records'][r]
            result_box(xc, yy, R['ran_it'], R['result'])
            drawn.add((R['ran_it'], R['result'] if R['ran_it'] != 'not run' else ''))
            (rec[f'ran_{r}'], rec[f'result_{r}']) = (R['ran_it'], R['result'])
        n = c['records']['A']['adverse_rows_n']
        if n['possible']:
            dx.text(xc, 3, bound(n), ha='center', va='center', fontsize=FS)
        else:
            dx.text(xc, 3, '–', ha='center', va='center', fontsize=FS, color=G1)
        for (r, yk) in (('A', 2), ('B', 1)):
            R = c['records'][r]
            k = R['adverse_on_proposed_cause_and_quantity']
            if n['possible']:
                dx.text(xc, yk, bound(k), ha='center', va='center', fontsize=FS, color=MUTE)
            (rec[f'adverse_on_named_{r}'], rec[f'adverse_rows_{r}']) = (k, R['adverse_rows_n'])
        rec['holds_a_result_left_open'] = bool(c['uncertain_adverse_rows'])
        plotted['b'][c['case']] = rec
    xh = [xs[c['case']] for c in cases if c['group'] == 'H']
    xp = [xs[c['case']] for c in cases if c['group'] == 'P']
    dx.set_xlim(-0.55, x - 0.45)
    dx.set_ylim(0.5, 9.6)
    dx.axis('off')
    for (xx, lab) in ((xh, 'not used to write step 5'), (xp, 'used to write step 5')):
        dx.plot([xx[0] - 0.35, xx[-1] + 0.35], [0.3, 0.3], color=G1, lw=0.6, clip_on=False)
        dx.text((xx[0] + xx[-1]) / 2, -0.25, lab, ha='center', va='center', fontsize=FS, color=MUTE, clip_on=False)
    (ly1, ly2, ly3) = (fy(141.0), fy(145.8), fy(150.0))
    items = [('box', 'step 5: unknown'), ('dot', 'passes agree'), ('ring', 'passes differ')]
    for ran in ('in full', 'in part'):
        for res_ in ('favourable', 'adverse', 'mixed'):
            if (ran, res_) in drawn:
                items.append((res_, f'run {ran}: {res_}'))
    if ('not run', '') in drawn:
        items.append(('notrun', 'not run'))
    (lx, row) = (4.0, ly1)
    for (kind, lab) in items:
        if lab.startswith('run') and row == ly1:
            (lx, row) = (4.0, ly2)
        ly = row
        (x0, y0, w, h) = (fx(lx), ly - 1.4 / H, fx(2.8), 2.8 / H)
        T = fig.transFigure
        if kind == 'box':
            fig.patches.append(Rectangle((x0, y0), w, h, transform=T, fc='white', ec=INK, lw=0.6))
        elif kind == 'dot':
            fig.lines.append(plt.Line2D([x0 + w / 2], [ly], transform=T, marker='o', ms=5, mfc=INK, mec=INK, ls=''))
        elif kind == 'ring':
            fig.lines.append(plt.Line2D([x0 + w / 2], [ly], transform=T, marker='o', ms=3.2, mfc='white', mec=G1, mew=0.6, ls=''))
        elif kind == 'mixed':
            fig.patches.append(Polygon([(x0, y0), (x0, y0 + h), (x0 + w, y0 + h)], transform=T, fc=BLUE, ec='none'))
            fig.patches.append(Polygon([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h)], transform=T, fc=RED, ec='none'))
        elif kind == 'notrun':
            fig.patches.append(Rectangle((x0, y0), w, h, transform=T, fc='white', ec=G1, lw=0.6))
        else:
            fig.patches.append(Rectangle((x0, y0), w, h, transform=T, fc=BLUE if kind == 'favourable' else RED, ec='none'))
        fig.text(fx(lx + 3.8), ly, lab, fontsize=FS, va='center')
        lx += 3.8 + 1.6 * len(lab) + 4.0
    fig.text(fx(4.0), ly3, 'a–b: range, where a result is uncertain;  –: no later adverse result', fontsize=FS, va='center', color=MUTE)
    plotted['b_legend'] = sorted((f'{a} | {b}' for (a, b) in drawn))
    json.dump(dict(script='code/figures/fig4_checklist.py', sources=['data/later_tests.json', 'data/checklist_cases.json'], **plotted), open(os.path.join(RES, 'fig4_values.json'), 'w'), indent=1, ensure_ascii=False)
    save(fig, 'fig4_checklist')
if __name__ == '__main__':
    main()
