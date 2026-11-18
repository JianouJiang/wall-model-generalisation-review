#!/usr/bin/env python3
"""Compare two wall-stress error measures and three outer-closure experiments."""
import json
import sys
from pathlib import Path

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import NullLocator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import DATA, RES, W, MM, FS, G2, INK, MUTE, plt, save

H = 110.0
BLUE = '#205991'
SLATE = '#80909a'
BAND = '#e8ebec'
RULE = '#8a959b'


def label(fig, x, y, value, **kwargs):
    return fig.text(x/W, 1-y/H, value, ha=kwargs.pop('ha', 'left'), va='center',
                    fontsize=kwargs.pop('fontsize', FS), color=kwargs.pop('color', INK), **kwargs)


def hline(fig, left, right, y, color=G2, width=0.55):
    fig.add_artist(Line2D([left/W, right/W], [1-y/H]*2, transform=fig.transFigure,
                          color=color, lw=width, solid_capstyle='butt'))


def axes(fig, x, y, width, height):
    return fig.add_axes([x/W, (H-y-height)/H, width/W, height/H])


def heading(fig, y, letter, title, source):
    label(fig, 1.3, y, letter, fontsize=10, fontweight='bold')
    label(fig, 6.2, y, title, fontsize=9.2, fontweight='bold')
    label(fig, 158.5, y, source, color=MUTE, ha='right')
    hline(fig, 1.3, 158.5, y+3.7, color=RULE)


def step_comparison(fig, data):
    heading(fig, 3.4, 'a', 'Backward-facing step with a graph wall model', 'Dupuy et al. (2023), Table 5')
    steps = np.asarray(data['message_passing_steps'])
    rows = np.arange(len(steps))
    magnitude = np.array(data['magnitude'])/data['baseline_magnitude']
    streamwise = np.array(data['streamwise_component'])/data['baseline_streamwise_component']
    top, height = 14.7, 22.4
    dy = height/len(rows)
    label(fig, 2, 11.0, 'Depth', fontweight='bold')
    for i, step in enumerate(steps):
        label(fig, 6, top+(i+.5)*dy, str(step), ha='center',
              color=BLUE if step == 4 else INK, fontweight='bold' if step == 4 else 'normal')
    panels = [(18, 'Wall-stress magnitude', magnitude), (91, 'Streamwise component', streamwise)]
    for left, title, fractions in panels:
        width = 52
        label(fig, left, 11.0, title, fontweight='bold')
        ax = axes(fig, left, top, width, height)
        ax.set(xlim=(0, 1.015), ylim=(len(rows)-.5, -.5), yticks=[], xticks=[0, .5, 1])
        ax.set_xticklabels(['0', '0.5', '1'])
        ax.tick_params(axis='x', pad=2)
        for spine in ('top','right','left'):
            ax.spines[spine].set_visible(False)
        ax.spines['bottom'].set_color(RULE)
        ax.axvline(.5, color=G2, lw=.45, zorder=0)
        ax.axvline(1, color=RULE, lw=.65, ls=(0, (2.5, 2.3)), zorder=0)
        ax.barh(rows, fractions, height=.47, color=[BLUE if step==4 else SLATE for step in steps],
                zorder=2, linewidth=0)
        for i, value in enumerate(fractions):
            focus = steps[i] == 4
            label(fig, left+width+9.5, top+(i+.5)*dy, f'{value:.3f}', ha='right',
                  color=BLUE if focus else MUTE, fontweight='bold' if focus else 'normal')
    label(fig, W/2, 44.8, 'Integrated squared wall-stress error / law-of-the-wall baseline', ha='center')
    return magnitude, streamwise


def boundary_layer(fig, outer):
    heading(fig, 50.7, 'b', 'Wall stress in a zero-pressure-gradient boundary layer', 'Lozano-Durán & Bae (2023), Fig. 9')
    readings = outer['station_readings']
    station = np.asarray(readings['re_x'])/1e5
    low, high = outer['total_error']['reported_range_percent']
    methods = [('EQWM', 'Equilibrium wall law', 'o', INK, 'white', '--'),
               ('BFWM', 'Building-block wall law', 'D', BLUE, BLUE, '-')]
    for (key, title, marker, color, face, ls), x in zip(methods, (3, 53)):
        y = 58.2
        mark = Line2D([(x+3.4)/W], [1-y/H], transform=fig.transFigure, marker=marker,
                      ms=3.8, markeredgewidth=.9, markerfacecolor=face, markeredgecolor=color,
                      linestyle='none', zorder=4)
        fig.add_artist(Line2D([x/W,(x+6.8)/W], [1-y/H]*2, transform=fig.transFigure,
                              color=color, lw=.85, ls=ls))
        fig.add_artist(mark)
        label(fig, x+8.2, y, title)
    fig.add_artist(Rectangle((106.8/W, 1-59.4/H), 5.7/W, 2.5/H, transform=fig.transFigure,
                             facecolor=BAND, edgecolor='#a2a7a8', linewidth=.4))
    label(fig, 114.0, 58.2, f'Authors’ {low:g}–{high:g}% summary')
    label(fig, 33.3, 63.5, 'Internal error', ha='center', fontweight='bold')
    label(fig, 108, 63.5, 'Total error', ha='center', fontweight='bold')
    hline(fig, 15.5, 53, 65.8)
    hline(fig, 65, 153, 65.8)

    experiments = [('Exact for the mean', 17), ('Dynamic Smagorinsky', 66.5), ('Vreman', 116)]
    plot_width, top, height = 36, 71.2, 29.1
    for j, (closure, left) in enumerate(experiments):
        label(fig, left+plot_width/2, 68.5, closure, ha='center')
        ax = axes(fig, left, top, plot_width, height)
        ax.set_yscale('log')
        ax.set(xlim=(5.65, 12.35), ylim=(.16, 32), xticks=station,
               yticks=[.2, 1, 5, 20])
        ax.set_xticklabels([f'{s:g}' for s in station])
        ax.set_yticklabels(['0.2', '1', '5', '20'])
        ax.yaxis.set_minor_locator(NullLocator())
        ax.tick_params(axis='x', pad=2)
        ax.tick_params(axis='y', length=2.5 if j==0 else 0, labelleft=(j==0), pad=2)
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
        ax.spines['bottom'].set_color(RULE)
        ax.spines['left'].set_visible(j==0)
        if j:
            ax.axhspan(low, high, fc=BAND, ec='none', zorder=0)
        for level in (1, 5, 20):
            ax.axhline(level, color='#c9cdcf', lw=.45, zorder=1)
        for key, _, marker, color, face, line_style in methods:
            values = next(s['error_percent_approx'] for s in readings['series']
                          if s['wall_model']==key and s['outer_closure']==closure)
            ax.plot(station, values, linestyle=line_style, marker=marker, ms=3.9,
                    linewidth=.85, color=color, mec=color, mfc=face, mew=.85, zorder=3)
    label(fig, 2.8, top+height/2, 'Error (%, log scale)', rotation=90, ha='center')
    label(fig, W/2, 107.7, r'Streamwise Reynolds number, $Re_x/10^5$', ha='center')


def main():
    revision = Path(DATA)/'revision'
    dupuy = json.loads((revision/'dupuy_table5.json').read_text())
    outer = json.loads((revision/'outer_input_error.json').read_text())
    fig = plt.figure(figsize=(W*MM, H*MM))
    magnitude, streamwise = step_comparison(fig, dupuy)
    boundary_layer(fig, outer)
    save(fig, 'fig3_contrast')
    values = dict(source=dupuy['doi'], table=5, x=dupuy['message_passing_steps'],
                  magnitude_ratio=magnitude.tolist(), streamwise_ratio=streamwise.tolist(),
                  outer_input_comparison=outer)
    (Path(RES)/'fig3_values.json').write_text(json.dumps(values, indent=2, ensure_ascii=False)+'\n')


if __name__ == '__main__':
    main()
