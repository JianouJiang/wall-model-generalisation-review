#!/usr/bin/env python3
"""Research figure rendering from the accompanying public data."""
import csv, json, os, re
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from style import *
KINDS = [('observable', 'quantity examined'), ('location', 'location'), ('flow parameter', 'flow parameter'), ('flow configuration', 'type of flow'), ('numerics', 'numerical set-up')]
REFINED = {'N626': dict(coarse=('τ', 'τ'), drawn=('$|\\tau|$', '$\\tau_x$'), favourable='magnitude of the wall stress (Sec. 4.2.3, Fig. 15 of the source)', adverse='streamwise component of the wall stress, with the reattachment point (Sec. 4.2.3, Fig. 16)', pair='N626-04')}

def macros():
    t = open(os.path.join(PROJECT, 'manuscript', 'numbers.tex'), encoding='utf-8').read()
    return {k: v for (k, v) in re.findall('\\\\newcommand\\{\\\\(n\\w+)\\}\\{([^}]*)\\}', t)}

def main():
    mix = json.load(open(os.path.join(DATA, 'contrasts.json')))
    qp = {c['study_id']: c for c in json.load(open(os.path.join(DATA, 'quantity_pairs.json'), encoding='utf-8'))['claims']}
    corpus = {r['study_id']: r for r in csv.DictReader(open(os.path.join(DATA, 'studies.csv')))}
    printed = printed_refs()
    M = macros()

    def label(sid, mark=''):
        ref = printed[corpus[sid]['bib_key']]
        return f"{ref['surname']} {ref['year']}{mark}" + (f" [{ref['n']}]" if ref.get('n') else '')
    claims = mix['claims_table']
    conf = [c for c in claims if c['category_2_confirmed']]
    totals = [(lab, sum((c[k]['confirmed'] for c in conf))) for (k, lab) in KINDS]
    totals.append(('two or more factors only', sum((c['confounded_only']['confirmed'] for c in conf))))
    expect = [M['nObs'], M['nLoc'], M['nPar'], M['nCfg'], M['nNum'], M['nConf']]
    assert [str(v) for (_, v) in totals] == expect, (totals, expect)
    assert str(len(conf)) == M['nM'], (len(conf), M['nM'])
    fig = plt.figure(figsize=(W * MM, 112 * MM))
    ax = fig.add_axes([0.255, 0.49, 0.19, 0.36])
    n = len(totals)
    for (i, (lab, v)) in enumerate(totals):
        y = n - 1 - i
        col = INK if i == 0 else G1 if i == n - 1 else MUTE
        ax.barh(y, v, height=0.62, color=BLUE if i == 0 else G2 if i == n - 1 else G1, lw=0)
        ax.text(v + 0.3, y, str(v), va='center', ha='left', fontsize=FS, color=INK, fontweight='bold' if i == 0 else 'normal')
        ax.text(-0.4, y, lab, va='center', ha='right', fontsize=FS, color=INK)
    ax.set_xlim(0, 10.5)
    ax.set_ylim(-0.6, n - 0.4)
    ax.axis('off')
    letter(fig, 0.012, 0.955, 'a')
    fig.text(0.04, 0.955, f'{len(conf)} claims held where they could fail\nand also met an adverse coupled result.\nTheir two results differ only in:', fontsize=FS, va='top', linespacing=1.15)
    lg = fig.add_axes([0.012, 0.01, 0.44, 0.4])
    lg.axis('off')
    lg.set_xlim(0, 1)
    lg.set_ylim(0, 7)
    items = [('dot', 'one factor alone separates the results'), ('ring', 'the same, both against a matched baseline'), ('open', 'possible, not certain'), ('sq', 'every pair differs in two or more factors')]
    for (j, (kind, lab)) in enumerate(items):
        yy = 6.3 - j * 0.95
        if kind == 'dot':
            lg.plot(0.035, yy, 'o', ms=5, mfc=INK, mec=INK)
        elif kind == 'ring':
            lg.plot(0.035, yy, 'o', ms=5, mfc=INK, mec=INK)
            lg.plot(0.035, yy, 'o', ms=8.5, mfc='none', mec=INK, mew=0.7)
        elif kind == 'open':
            lg.plot(0.015, yy, 'o', ms=5, mfc='white', mec=INK, mew=0.7)
            lg.plot(0.05, yy, 's', ms=4.6, mfc='white', mec=G1, mew=0.7)
            lg.plot(0.092, yy, 'o', ms=8.5, mfc='none', mec=G1, mew=0.7)
        else:
            lg.plot(0.035, yy, 's', ms=4.6, mfc=G1, mec=G1)
        lg.text(0.13 if kind == 'open' else 0.08, yy, lab, va='center', fontsize=FS)
    yy = 6.3 - 4 * 0.95
    lg.text(0.012, yy, 'τ', va='center', fontsize=FS, color=BLUE)
    lg.text(0.04, yy, '|', va='center', fontsize=FS, color=G1)
    lg.text(0.055, yy, 'U', va='center', fontsize=FS, color=RED)
    lg.text(0.1, yy, 'quantity: favourable | adverse', va='center', fontsize=FS)
    lg.text(0.012, yy - 0.95, 'S, R, L: wall-stress, RANS, learned', va='center', fontsize=FS, color=MUTE)
    lg.text(0.012, yy - 1.9, '*: pilot study;  grey name: uncertain', va='center', fontsize=FS, color=MUTE)
    order = sorted(claims, key=lambda c: (not c['category_2_confirmed'], -sum((c[k]['confirmed'] for (k, _) in KINDS)), [not c[k]['confirmed'] for (k, _) in KINDS], c['study_id']))
    bx = fig.add_axes([0.665, 0.01, 0.3, 0.775])
    N = len(order)
    plotted = {}
    COLX = [0, 1, 2, 3, 4, 5.25]
    for (i, c) in enumerate(order):
        y = N - 1 - i
        m = corpus[c['study_id']]
        cls = {'wall-stress model for LES': 'S', 'RANS wall function': 'R', 'learned': 'L', 'inner-outer': 'I'}[m['treatment_class_S1']]
        star = '' if c['set'] == 'new' else '*'
        okc = INK if c['category_2_confirmed'] else G1
        bx.text(-1.25, y, label(c['study_id'], star), ha='right', va='center', fontsize=FS, color=okc)
        bx.text(-0.8, y, cls, ha='center', va='center', fontsize=FS, color=MUTE)
        if i % 2 == 0:
            bx.add_patch(Rectangle((-0.5, y - 0.5), 9.0, 1, fc=BAND, ec='none', zorder=0, clip_on=False))
        rec = dict(set=c['set'], confirmed_category_2=c['category_2_confirmed'])
        for (j, (k, _)) in enumerate(KINDS):
            if c[k]['confirmed']:
                bx.plot(j, y, 'o', ms=5, mfc=INK, mec=INK, zorder=3)
                if c[k]['doubly_matched_confirmed']:
                    bx.plot(j, y, 'o', ms=8.5, mfc='none', mec=INK, mew=0.7, zorder=3)
                elif c[k].get('doubly_matched_possible'):
                    bx.plot(j, y, 'o', ms=8.5, mfc='none', mec=G1, mew=0.7, zorder=3)
                    rec.setdefault('both_sides_matched_possibly', []).append(k)
                rec[k] = 'confirmed, both sides matched' if c[k]['doubly_matched_confirmed'] else 'confirmed'
            elif c[k]['possible']:
                bx.plot(j, y, 'o', ms=5, mfc='white', mec=INK, mew=0.7, zorder=3)
                rec[k] = 'possible'
        if c['confounded_only']['confirmed']:
            bx.plot(COLX[5], y, 's', ms=4.6, mfc=G1, mec=G1, zorder=3)
            rec['two or more only'] = 'confirmed'
        elif c['confounded_only']['possible']:
            bx.plot(COLX[5], y, 's', ms=4.6, mfc='white', mec=G1, mew=0.7, zorder=3)
            rec['two or more only'] = 'possible'
        if c['study_id'] in qp:
            q = qp[c['study_id']]
            (fav, adv) = (', '.join(q['letters_favourable']), ', '.join(q['letters_adverse']))
            if c['study_id'] in REFINED:
                assert (fav, adv) == REFINED[c['study_id']]['coarse'], (c['study_id'], fav, adv)
                (fav, adv) = REFINED[c['study_id']]['drawn']
                rec['quantities_drawn_finer'] = REFINED[c['study_id']]
            bx.text(7.05, y, fav, ha='right', va='center', fontsize=FS, color=BLUE)
            bx.text(7.25, y, '|', ha='center', va='center', fontsize=FS, color=G1)
            bx.text(7.45, y, adv, ha='left', va='center', fontsize=FS, color=RED)
            (rec['quantities_favourable'], rec['quantities_adverse']) = (q['favourable_groups'], q['adverse_groups'])
        plotted[c['study_id']] = rec
    heads = [lab for (_, lab) in KINDS] + ['two or more', 'quantities']
    for (xx, lab) in zip(COLX + [7.25], heads):
        bx.text(xx - 0.15, N - 0.2, lab, rotation=50, ha='left', va='bottom', fontsize=FS, color=INK, rotation_mode='anchor')
    bx.set_xlim(-0.5, 8.6)
    bx.set_ylim(-0.6, N - 0.4)
    bx.axis('off')
    letter(fig, 0.47, 0.955, 'b')
    json.dump(dict(script='code/figures/fig3_contrast.py', totals=totals, matrix=plotted), open(os.path.join(RES, 'fig3_values.json'), 'w'), indent=1, ensure_ascii=False)
    save(fig, 'fig3_contrast')
if __name__ == '__main__':
    main()
