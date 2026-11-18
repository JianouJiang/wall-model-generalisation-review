#!/usr/bin/env python3
"""Research figure rendering from the accompanying public data."""
import json
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib._mathtext as _mathtext
(_mathtext.SHRINK_FACTOR, _mathtext.GROW_FACTOR) = (0.75, 1 / 0.75)
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import layout
import text_inventory
PROJECT = os.path.abspath(os.path.join(HERE, '..', '..'))
DATA = os.path.join(PROJECT, 'data')
RES = os.path.join(PROJECT, 'results', 'figures')
os.makedirs(RES, exist_ok=True)
OUT = os.path.join(PROJECT, 'figures')
os.makedirs(OUT, exist_ok=True)
MM = 1 / 25.4
W = 160.0
FS = 8.0
FS_LETTER = 10.0
(BLUE, RED) = ('#2a78d6', '#e34948')
(G1, G2, G3, INK, MUTE, BAND) = ('#8c8b86', '#c9c8c2', '#ffffff', '#0b0b0b', '#52514e', '#f2f1ee')
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': FS, 'axes.linewidth': 0.6, 'pdf.fonttype': 42, 'mathtext.fontset': 'dejavusans', 'xtick.labelsize': FS, 'ytick.labelsize': FS, 'axes.labelsize': FS, 'xtick.major.width': 0.6, 'xtick.major.size': 2.5, 'ytick.major.size': 0, 'hatch.linewidth': 0.4, 'svg.hashsalt': 'wmr', 'pdf.compression': 6})

def letter(fig, x, y, s, title=None):
    fig.text(x, y, s, fontsize=FS_LETTER, fontweight='bold', va='baseline')
    if title:
        fig.text(x + 0.022, y, title, fontsize=FS, va='baseline', color=INK)

def check_sizes(fig, name):
    import matplotlib.text as mtext
    (small, n) = ([], 0)
    for t in fig.findobj(mtext.Text):
        if t.get_visible() and t.get_text().strip():
            n += 1
            if t.get_fontsize() < FS - 1e-06:
                small.append((t.get_text(), t.get_fontsize()))
    assert not small, f'{name}: text below {FS} pt: {small[:8]}'
    return n

def save(fig, name, allow=()):
    n = check_sizes(fig, name)
    lay = layout.layout(fig)
    (used, viol) = (set(), [])
    for kind in ('clipped', 'crossings', 'text_overlaps'):
        for v in lay[kind]:
            hit = [i for (i, (a, b, _)) in enumerate(allow) if a in (v['text'], v.get('gid')) and b in v.get('other', '')]
            if hit and kind != 'clipped':
                used.update(hit)
                v['allowed'] = allow[hit[0]][2]
            else:
                viol.append((kind, v))
    stale = [allow[i] for i in range(len(allow)) if i not in used]
    lay.update(figure=name, declared_exceptions=[dict(text=a, other=b, reason=c) for (a, b, c) in allow], exceptions_matching_nothing=[list(s) for s in stale], violations=len(viol), passed=not viol and (not stale))
    json.dump(lay, open(os.path.join(RES, f'{name}_layout.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    assert not viol, f'{name}: layout rule broken ({len(viol)}): {viol}'
    assert not stale, f'{name}: declared layout exceptions that match nothing: {stale}'
    text_inventory.dump(fig, os.path.join(RES, f'{name}_text.json'), name)
    p = os.path.join(OUT, name + '.pdf')
    fig.savefig(p, metadata={'CreationDate': None, 'Producer': None, 'Creator': None})
    print(f'written {os.path.relpath(p, PROJECT)} ({n} texts, all >= {FS} pt; layout rules passed)')

def printed_refs():
    p = os.path.join(DATA, 'reference_labels.json')
    return json.load(open(p, encoding='utf-8'))['entries']
