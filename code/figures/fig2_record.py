#!/usr/bin/env python3
"""Selected comparison designs across the review; no population counts."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from matplotlib.patches import Rectangle
from style import *


def main():
    d = json.load(open(os.path.join(DATA, 'revision/comparison_map.json')))
    support = {r['claim_id']: r for r in json.load(open(os.path.join(DATA, 'revision/claim_support.json')))}
    H = 102.0
    fig = plt.figure(figsize=(W * MM, H * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, W), ylim=(H, 0))
    ax.axis('off')
    letter(fig, 0.012, 1-5/H, 'a', 'What changes')
    letter(fig, 0.656, 1-5/H, 'b', 'What is examined')
    # Retain the original figure family's aligned, banded matrix.
    cx = [58, 67, 76, 85, 94]
    qx = [108, 117, 126, 135, 144]
    for xs, names in [(cx, d['change_columns']), (qx, d['quantity_columns'])]:
        for x, lab in zip(xs, names):
            ax.text(x-1.1, 30, lab, rotation=55, rotation_mode='anchor',
                    ha='left', va='bottom', fontsize=FS)
    plotted = []
    for i, row in enumerate(d['rows']):
        assert all(s in support and support[s]['reference_key'] == row['reference_key'] for s in row['support'])
        y = 35 + i * 6.7
        if i % 2 == 0:
            ax.add_patch(Rectangle((1.4, y-3.1), 153.6, 6.2, fc=BAND, ec='none', zorder=0))
        ax.text(51.6, y, row['label'], ha='right', va='center', fontsize=FS)
        for x, field in zip(cx, d['change_columns']):
            if field in row['changes']:
                ax.plot(x, y, 'o', ms=4.8, mfc=INK, mec=INK, zorder=3)
        for x, field in zip(qx, d['quantity_columns']):
            if field in row['quantities']:
                ax.plot(x, y, 's', ms=4.5, mfc=BLUE, mec=BLUE, zorder=3)
        plotted.append(row)
    ax.plot([101, 101], [32, 85.1], color=G2, lw=.6)
    ax.plot(3.1, 89.8, 'o', ms=4.8, mfc=INK, mec=INK)
    ax.text(5.9, 89.8, 'changed in the selected comparison', va='center', fontsize=FS)
    ax.plot(76.5, 89.8, 's', ms=4.5, mfc=BLUE, mec=BLUE)
    ax.text(79.5, 89.8, 'reported quantity', va='center', fontsize=FS)
    ax.text(1.4, 96.6, '* preprint; † accepted manuscript. Blank: not tabulated for this example.',
            va='center', fontsize=FS, color=MUTE)
    with open(os.path.join(RES, 'fig2_values.json'), 'w') as f:
        json.dump(dict(purpose=d['purpose'], blank_meaning=d['blank_meaning'], rows=plotted), f, indent=2, ensure_ascii=False)
    save(fig, 'fig2_record')


if __name__ == '__main__':
    main()
