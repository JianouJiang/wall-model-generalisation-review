#!/usr/bin/env python3
"""Research figure rendering from the accompanying public data."""
import json
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
from style import *
CLASSES = [('wall-stress model for LES', 'Wall-stress models for LES'), ('RANS wall function', 'RANS wall functions'), ('learned', 'Learned wall models')]
CATS = [('held', ('1a', '1b')), ('mixed', ('2',)), ('adverse', ('3',)), ('unknown', ('5',)), ('not exposed', ('6',)), ('open', ('undetermined',))]
LABS = {'held': 'held where it could fail', 'mixed': 'held, but also adverse', 'adverse': 'adverse, without holding', 'unknown': 'unclear if a test could fail', 'not exposed': 'no test that could fail', 'open': 'uncertain'}
BIN_OF = {k: name for (name, ks) in CATS[:-1] for k in ks}

def drawn_bin(between):
    bins = {BIN_OF.get(k) for k in between}
    return bins.pop() if len(bins) == 1 and None not in bins else 'open'

def seg(ax, x, y, w, h, kind):
    if w <= 0:
        return
    if kind == 'mixed':
        ax.add_patch(Rectangle((x, y + h / 2), w, h / 2, fc=BLUE, ec='none'))
        ax.add_patch(Rectangle((x, y), w, h / 2, fc=RED, ec='none'))
        ax.add_patch(Rectangle((x, y), w, h, fc='none', ec='white', lw=0.8))
    elif kind == 'open':
        ax.add_patch(Rectangle((x, y), w, h, fc=G3, ec=G1, lw=0.6))
    else:
        fc = {'held': BLUE, 'adverse': RED, 'unknown': G1, 'not exposed': G2}[kind]
        ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec='white', lw=0.8))

def counts(block, ids=None):
    cats = block['categories']
    vals = {name: sum((cats.get(k, 0) for k in ks)) for (name, ks) in CATS[:-1]}
    vals['open'] = 0
    moved = []
    for u in block['undetermined_list']:
        if ids is not None and u['study_id'] not in ids:
            continue
        b = drawn_bin(u['between'])
        vals[b] += 1
        if b != 'open':
            moved.append(dict(study_id=u['study_id'], between=u['between'], drawn_as=b))
    return (vals, moved)

def main():
    syn = json.load(open(os.path.join(DATA, 'claim_categories.json')))
    (plotted, moved_all) = ({}, {})
    fig = plt.figure(figsize=(W * MM, 62 * MM))
    ax = fig.add_axes([0.3, 0.16, 0.68, 0.6])
    rows = [('All claims', None)] + [(lab, key) for (key, lab) in CLASSES]
    for (i, (lab, key)) in enumerate(rows):
        y = len(rows) - 1 - i
        for (which, h, y0) in (('pooled', 0.46, y + 0.04), ('new', 0.2, y - 0.22)):
            a6 = syn[which]['categories']
            und = a6['category_undetermined']
            if key is None:
                (vals, moved) = counts(dict(categories=a6['categories'], undetermined_list=und))
                total_expected = a6['claims']
            else:
                c = a6['by_class'][key]
                (vals, moved) = counts(dict(categories=c['categories'], undetermined_list=und), set(c['study_ids']))
                total_expected = c['studies']
                assert vals['open'] + len(moved) == c['categories'].get('undetermined', 0), (key, which)
            x = 0
            for (name, _) in CATS:
                n = vals[name]
                seg(ax, x, y0, n, h, name)
                if which == 'pooled' and n >= 2:
                    ax.text(x + n / 2, y0 + h / 2, str(n), ha='center', va='center', fontsize=FS, color='white' if name in ('held', 'adverse', 'unknown') else INK, bbox=dict(fc='white', ec='none', pad=0.5, alpha=0.9) if name == 'mixed' else None, gid='count of a two-colour segment' if name == 'mixed' else None)
                x += n
            assert x == total_expected, (lab, which, x, total_expected)
            plotted[f'{lab} | {which}'] = dict(vals, total=x)
            if moved:
                moved_all[f'{lab} | {which}'] = moved
            if which == 'pooled':
                ax.text(-1.2, y0 + h / 2, f'{lab} ({x})', ha='right', va='center', fontsize=FS, color=INK)
            else:
                ax.text(-1.2, y0 + h / 2, f'excluding pilot ({x})', ha='right', va='center', fontsize=FS, color=MUTE)
    ax.set_xlim(0, 84)
    ax.set_ylim(-0.5, len(rows) - 0.42)
    ax.set_yticks([])
    ax.set_xticks([0, 20, 40, 60, 80])
    ax.set_xlabel('claimed improvements', labelpad=2)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    lax = fig.add_axes([0.02, 0.8, 0.96, 0.19])
    lax.axis('off')
    lax.set_xlim(0, 1)
    lax.set_ylim(0, 2)
    xs = [0.0, 0.36, 0.7]
    for (j, (name, _)) in enumerate(CATS):
        (cx, cy) = (xs[j % 3], 1 - j // 3)
        seg(lax, cx, cy + 0.25, 0.028, 0.5, name)
        lax.text(cx + 0.04, cy + 0.5, LABS[name], va='center', fontsize=FS)
    json.dump(dict(script='code/figures/fig2_record.py', source='data/claim_categories.json', bin_rule='an uncertain claim is drawn in a bin only when every category it may take lies in that bin; otherwise `open` (drawn white, `uncertain`)', bars=plotted, uncertain_claims_drawn_in_a_bin=moved_all, legend=[LABS[n] for (n, _) in CATS]), open(os.path.join(RES, 'fig2_values.json'), 'w'), indent=1, ensure_ascii=False)
    save(fig, 'fig2_record', allow=[('count of a two-colour segment', 'Rectangle', 'the count of a segment `held, but also adverse` sits on its own white box inside that segment, across the line between its blue and red halves')])
if __name__ == '__main__':
    main()
