#!/usr/bin/env python3
"""Published comparisons distinguish baseline improvement and outer-input error."""
import json
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from matplotlib.patches import FancyArrowPatch
from style import *


def main():
    d = json.load(open(os.path.join(DATA, 'revision/dupuy_table5.json')))
    outer = json.load(open(os.path.join(DATA, 'revision/outer_input_error.json')))
    H = 78.
    fig = plt.figure(figsize=(W * MM, H * MM))
    letter(fig, .012, 1-5/H, 'a', 'Improvement over a baseline')
    letter(fig, .605, 1-5/H, 'b', 'Internal and total error')
    ax = fig.add_axes([.09, .22, .438, .58])
    x = np.asarray(d['message_passing_steps'])
    y1 = np.asarray(d['magnitude']) / d['baseline_magnitude']
    y2 = np.asarray(d['streamwise_component']) / d['baseline_streamwise_component']
    ax.axvspan(3.84, 4.16, color=BAND, lw=0, zorder=0)
    ax.axhline(1, color=G1, lw=.7, ls=(0, (4, 3)), zorder=1)
    ax.text(.87, 1.025, 'law-of-the-wall baseline', va='bottom', fontsize=FS, color=MUTE)
    ax.plot(x, y1, 'o-', color=BLUE, ms=3.8, lw=1.05, zorder=3)
    ax.plot(x, y2, 's-', color=RED, ms=3.8, lw=1.05, zorder=3)
    ax.text(3.72, .16, f'{y1[3]:.3f}', ha='right', va='bottom', color=BLUE, fontsize=FS)
    ax.text(4.23, .57, f'{y2[3]:.3f}', ha='left', va='bottom', color=RED, fontsize=FS)
    ax.set(xlim=(.7, 5.35), ylim=(0, 1.11), xticks=x,
           yticks=[0, .25, .5, .75, 1], xlabel='message-passing steps',
           ylabel='squared-error integral / baseline')
    ax.set_yticklabels(['0', '0.25', '0.50', '0.75', '1'])
    for side in ('right', 'top'):
        ax.spines[side].set_visible(False)
    lg = fig.add_axes([.09, .83, .44, .055])
    lg.set(xlim=(0, 1), ylim=(0, 1)); lg.axis('off')
    lg.plot([0, .055], [.5, .5], color=BLUE, lw=1.05)
    lg.plot(.0275, .5, 'o', ms=3.8, color=BLUE)
    lg.text(.08, .5, 'magnitude', va='center', fontsize=FS)
    lg.plot([.49, .545], [.5, .5], color=RED, lw=1.05)
    lg.plot(.5175, .5, 's', ms=3.8, color=RED)
    lg.text(.57, .5, 'streamwise', va='center', fontsize=FS)

    # Preserve the source's bound, approximate value and range, rather than
    # manufacturing point samples from its narrative summary.
    bx = fig.add_axes([.625, .22, .355, .58])
    bx.set(xlim=(-.5, 16.5), ylim=(0, 3.8), xticks=[0, 5, 10, 15], yticks=[],
           xlabel='wall-stress error (%)')
    for side in ('left', 'right', 'top'):
        bx.spines[side].set_visible(False)
    bx.axhspan(1.83, 3.8, fc=BAND, lw=0, zorder=0)
    bx.text(0, 3.48, 'Exact-for-mean outer closure', va='center', fontsize=FS)
    upper = outer['internal_error']['BFWM']['value']
    approx = outer['internal_error']['EQWM']['value']
    bx.plot([upper, upper], [2.70, 2.94], color=INK, lw=.8, zorder=3)
    bx.add_patch(FancyArrowPatch((upper, 2.82), (0, 2.82), arrowstyle='-|>',
                                mutation_scale=6, color=INK, lw=.8, shrinkA=0, shrinkB=0))
    bx.text(3.2, 2.82, f'BFWM: <{upper:g}%', va='center', fontsize=FS)
    bx.plot(approx, 2.19, 'D', color=INK, ms=4.2, zorder=3)
    bx.text(3.2, 2.19, f'EQWM: ≈{approx:g}%', va='center', fontsize=FS)
    bx.text(0, 1.45, 'Practical outer closures', va='center', fontsize=FS)
    lo, hi = outer['total_error']['reported_range_percent']
    bx.plot([lo, hi], [.58, .58], color=INK, lw=2, solid_capstyle='butt', zorder=3)
    for end in (lo, hi):
        bx.plot([end, end], [.46, .70], color=INK, lw=.8, zorder=3)
    bx.text((lo+hi)/2, .97, f'both models: {lo:g}–{hi:g}%', ha='center', va='center', fontsize=FS)
    fig.text(.09, .055, 'Dupuy et al. (2023), Table 5', fontsize=FS, color=MUTE, va='center')
    fig.text(.625, .055, 'Lozano-Durán & Bae (2023), §4.3', fontsize=FS, color=MUTE, va='center')
    assert (y1 < 1).all() and (y2 < 1).all()
    with open(os.path.join(RES, 'fig3_values.json'), 'w') as f:
        json.dump(dict(source=d['doi'], table=5, x=x.tolist(), magnitude_ratio=y1.tolist(),
                       streamwise_ratio=y2.tolist(), outer_input_comparison=outer), f, indent=2)
    save(fig, 'fig3_contrast')


if __name__ == '__main__':
    main()
