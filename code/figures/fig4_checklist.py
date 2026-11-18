#!/usr/bin/env python3
"""Case-level agreement; neither outcome scores nor predictive validation."""
import json
import os
import sys
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
from matplotlib.patches import Rectangle
from style import *


def main():
    cases = json.load(open(os.path.join(DATA, 'checklist_cases.json')))['cases']
    keys = ['same_cause', 'same_observable_class', 'same_factor']
    rows = [('Cause', lambda c: c['agreement'][keys[0]]),
            ('Quantity class', lambda c: c['agreement'][keys[1]]),
            ('Factor to vary', lambda c: c['agreement'][keys[2]]),
            ('All three', lambda c: all(c['agreement'][k] for k in keys))]
    assert len(cases) == 13
    assert all(c['records'][p]['step5_from_the_item_record'] == 'unknown' for c in cases for p in ('A', 'B'))
    H = 71.
    fig = plt.figure(figsize=(W*MM, H*MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, W), ylim=(H, 0)); ax.axis('off')
    letter(fig, .012, 1-5/H, 'a', 'Agreement in each case')
    letter(fig, .778, 1-5/H, 'b', 'Totals')
    xs = [45 + 5.6*i for i in range(13)]
    ax.text(38.5, 14.5, 'case', ha='right', va='center', color=MUTE, fontsize=FS)
    for i, x in enumerate(xs):
        ax.text(x, 14.5, str(i+1), ha='center', va='center', fontsize=FS)
    ax.text(137.6, 14.5, 'of 13 cases', ha='center', va='center', fontsize=FS, color=MUTE)
    counts = []
    ys = [23, 31, 39, 49]
    for j, ((lab, measure), y) in enumerate(zip(rows, ys)):
        if j % 2 == 0:
            ax.add_patch(Rectangle((41, y-3.7), 75, 7.4, fc=BAND, ec='none', zorder=0))
        ax.text(38.5, y, lab, ha='right', va='center', fontsize=FS,
                fontweight='bold' if j == 3 else 'normal')
        n = sum(bool(measure(c)) for c in cases); counts.append(n)
        for x, c in zip(xs, cases):
            same = measure(c)
            ax.plot(x, y, 'o', ms=4.8 if same else 3.2,
                    mfc=INK if same else 'white', mec=INK if same else G1, mew=.7, zorder=3)
        left, width = 124., 29.
        blue_width = width*n/13
        ax.add_patch(Rectangle((left, y-2.4), blue_width, 4.8, fc=BLUE, ec='none'))
        ax.add_patch(Rectangle((left+blue_width, y-2.4), width-blue_width, 4.8, fc=G2, ec='none'))
        ax.text(left+blue_width/2, y, str(n), ha='center', va='center', color='white', fontsize=FS)
        ax.text(left+(blue_width+width)/2, y, str(13-n), ha='center', va='center', color=INK, fontsize=FS)
    ax.plot([41, 116], [44, 44], color=G2, lw=.6)
    ax.plot(3, 59, 'o', ms=4.8, mfc=INK, mec=INK)
    ax.text(6.2, 59, 'same choice', va='center', fontsize=FS)
    ax.plot(42, 59, 'o', ms=3.2, mfc='white', mec=G1, mew=.7)
    ax.text(45.2, 59, 'different choice', va='center', fontsize=FS)
    ax.add_patch(Rectangle((94, 57.8), 2.4, 2.4, fc=BLUE, ec='none'))
    ax.text(98, 59, 'agree', va='center', fontsize=FS)
    ax.add_patch(Rectangle((119, 57.8), 2.4, 2.4, fc=G2, ec='none'))
    ax.text(123, 59, 'differ', va='center', fontsize=FS)
    ax.text(1.4, 67, 'Assurance withheld in every case. Agreement describes use; predictive value is unestablished.',
            va='center', fontsize=FS, color=MUTE)
    patterns = Counter(tuple(bool(c['agreement'][k]) for k in keys) for c in cases)
    with open(os.path.join(RES, 'fig4_values.json'), 'w') as f:
        json.dump(dict(cases=13, agreement=dict(zip([lab for lab, _ in rows], counts)),
                       case_order=[dict(number=i+1, case=c['case'], agreement=c['agreement']) for i,c in enumerate(cases)],
                       agreement_patterns=[dict(choices=list(k), count=v) for k,v in sorted(patterns.items())],
                       assurance='withheld in all 13 cases'), f, indent=2)
    save(fig, 'fig4_checklist')


if __name__ == '__main__':
    main()
