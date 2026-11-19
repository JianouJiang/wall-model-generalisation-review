#!/usr/bin/env python3
"""Eight source-level comparisons, paired by flow in a 160 mm vector figure."""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from matplotlib.patches import Rectangle
from style import BAND, BLUE, DATA, FS, G1, G2, INK, MM, MUTE, RES, W, panel_heading, plt, save

PANEL_W = 75.8
FIG_H = 128.0


def label(ax, x, y, text, **kwargs):
    return ax.text(x, y, text, va='center', ha=kwargs.pop('ha', 'left'),
                   fontsize=kwargs.pop('fontsize', FS), color=kwargs.pop('color', INK), **kwargs)


def line(ax, x, y, **kwargs):
    ax.plot(x, y, color=kwargs.pop('color', G2), lw=kwargs.pop('lw', 0.65),
            solid_capstyle='round', **kwargs)


def arrow(ax, start, end, y, color):
    ax.annotate('', xy=(end, y), xytext=(start, y),
                arrowprops=dict(arrowstyle='-|>', shrinkA=0, shrinkB=0,
                                mutation_scale=6.2, lw=0.8, color=color))


def geometry(ax, panel):
    # Only the walls and free-stream direction are sketched; there is no inferred flow field.
    start, end = 55.8, 75.1
    if panel == 'a':
        for y in (1.5, 6.8):
            line(ax, [start, end], [y, y], color=INK, lw=1.05)
    elif panel == 'b':
        line(ax, [start, end], [6.8, 6.8], color=INK, lw=1.05)
    elif panel == 'c':
        xs = [start + (end-start)*i/60 for i in range(61)]
        ys = [7.3 - 3.4*math.exp(-((x-66.9)/3.1)**2) for x in xs]
        line(ax, xs, ys, color=INK, lw=1.05)
    else:
        line(ax, [start, 59.5, 59.5, 64], [4.5, 4.5, 7, 7], color=INK, lw=1.05)
        line(ax, [66.5, 69, 73, end], [4.5, 4.5, 7, 7], color=INK, lw=1.05)
    if panel in 'abc':
        arrow(ax, start+1, start+7.2, 4.2 if panel == 'a' else 2.9, INK)


def study(ax, y, title, row):
    name = row['label'].replace('*)', ')*').replace('†)', ')†')
    label(ax, 0.8, y, title)
    label(ax, 0.8, y+4.8, name, color=MUTE)


def channel(ax, first, second):
    study(ax, 13.4, 'Sampling height (wall units, log scale)', first)
    record = first['figure_example']

    def height_x(wall_units):
        return 2 + 70 * math.log(wall_units / 125) / math.log(6300 / 125)

    lo, hi = record['training_height_wall_units']
    xlo, xhi = height_x(lo), height_x(hi)
    band_y = 31.2
    ax.add_patch(Rectangle((xlo, band_y-2.3), xhi-xlo, 4.6, fc=BAND, ec='none'))
    label(ax, (xlo+xhi)/2, band_y, f'Training {lo:,}–{hi:,}', ha='center')
    largest = max(m['height_wall_units'] for m in record['measurements'])
    line(ax, [xlo, height_x(largest)], [27.1, 27.1], color=G1)
    for measurement in record['measurements']:
        value = measurement['height_wall_units']
        x = height_x(value)
        label(ax, x, 23.4, f"{measurement['grid']} {value:,}", ha='center')
        line(ax, [x, x], [26.2, 28.0], color=INK, lw=1.25)
    for x in (xlo, xhi):
        line(ax, [x, x], [27.1, band_y-2.3], color=BLUE, lw=0.65)

    study(ax, 41.5, 'Signed error in mean wall stress (%)', second)
    # Same signed, linear percentage axis for all three meshes.
    def error_x(value):
        return 40.5 + value*24

    for i, pair in enumerate(second['figure_example']['measurements']):
        y = 51.4 + 4.4*i
        a, b = error_x(pair['coupled']), error_x(pair['offline_mean'])
        label(ax, 1.6, y, pair['mesh'])
        line(ax, [a, b], [y, y], color=G1, lw=1.25)
        ax.plot(a, y, 'o', ms=4.5, mfc='white', mec=INK, mew=1, zorder=4)
        ax.plot(b, y, 'D', ms=3.8, mfc=BLUE, mec=BLUE, zorder=4)
    line(ax, [error_x(0)]*2, [49.5, 61.6], color=G1, lw=0.6, ls=(0, (1.5, 2)))
    line(ax, [error_x(-1.2), error_x(1)], [62.3]*2, color=G1)
    for value, tick in ((-1, '−1'), (0, '0'), (1, '+1')):
        x = error_x(value)
        line(ax, [x, x], [62.3, 63.2], color=MUTE)
        label(ax, x, 65.5, tick, ha='center', color=MUTE)
    ax.plot(2.4, 69, 'o', ms=4.5, mfc='white', mec=INK, mew=1)
    label(ax, 5.1, 69, 'A posteriori')
    ax.plot(27.6, 69, 'D', ms=3.8, color=BLUE)
    label(ax, 30.5, 69, 'A priori, mean velocity')


def flat_plate(ax, first, second):
    study(ax, 13.4, 'Sign of mean chordwise skin friction', first)
    record = first['figure_example']
    cols = [46, 65]
    for x, angle in zip(cols, record['sweep_degrees']):
        label(ax, x, 23.4, f'{angle}° sweep', ha='center', color=MUTE)
    for i, entry in enumerate(record['measurements']):
        y = 27.3 + 4.25*i
        label(ax, 2.0, y, entry['model'])
        for x, sign in zip(cols, entry['signs']):
            label(ax, x, y, {None: '∼0', -1: '−', 1: '+'}[sign], ha='center')

    study(ax, 41.5, 'Wall-stress error at zero pressure gradient', second)
    label(ax, 2.0, 53.0, 'Outer closure')
    label(ax, 54.0, 53.0, 'Stress error')
    line(ax, [2, 74.5], [55.6]*2)
    for i, experiment in enumerate(second['figure_example']['measurements']):
        y = 59.0 + i*4.8
        label(ax, 2, y, experiment['outer_closure'])
        label(ax, 54, y, experiment['stress_error'])


def state(ax, x, y, reversed_flow):
    color = BLUE if reversed_flow else INK
    left, right = x, x+5
    arrow(ax, right if reversed_flow else left, left if reversed_flow else right, y, color)
    label(ax, right+2, y, 'Reversal' if reversed_flow else 'No reversal')


def speed_bump(ax, first, second):
    for row, top in ((first, 13.4), (second, 43.0)):
        example = row['figure_example']
        prescribed = 'wall_condition' in example
        condition = (f"First-cell mean velocity" if prescribed
                     else f"Predicted mean skin friction, {example['grid'].lower()} mesh")
        study(ax, top, condition, row)
        for i, entry in enumerate(example['measurements']):
            y = top+11.5 + i*5.2
            name = (f"{example['closure']}  c = {entry['coefficient']:.3f}" if prescribed
                    else entry['model'] + ' wall law')
            label(ax, 2, y, name)
            state(ax, 47, y, entry['reversal'])


def expansions(ax, first, second):
    study(ax, 13.4, r'Mean step reattachment, $x_r/h_s$', first)
    example = first['figure_example']
    def location_x(value):
        return 26 + 19*(value-4)

    for i, result in enumerate(example['crossings']):
        y = 23.4 + i*4.6
        val = result['x_over_hs_approx']
        x = location_x(val)
        label(ax, 2, y, result.get('display_label', result['treatment']))
        ref = result['treatment'] == 'Reference'
        color = INK if ref else BLUE
        ax.plot(x, y, 's' if ref else 'o', ms=4.2, mfc='white' if ref else color,
                mec=color, mew=0.9, zorder=3)
        label(ax, x+2.0, y, f'≈{val:.1f}')
    line(ax, [location_x(4), location_x(6.4)], [35.6]*2, color=G1)
    for value in (4, 5, 6):
        x = location_x(value)
        line(ax, [x, x], [35.6, 36.5], color=MUTE)
        label(ax, x, 38.7, str(value), ha='center', color=MUTE)

    study(ax, 43.0, 'Recirculation on the inclined diffuser wall', second)
    for x, heading in ((2, 'Treatment'), (28.0, 'Cells in y'), (49.5, 'Recirculation')):
        label(ax, x, 53.2, heading)
    line(ax, [2, 74.5], [55.6]*2)
    for i, entry in enumerate(second['figure_example']['measurements']):
        y = 59 + i*5
        label(ax, 2, y, entry['model'])
        label(ax, 33.4, y, str(entry['cells_y']), ha='center')
        label(ax, 49.5, y, 'Present' if entry['recirculation'] else 'Absent')


def main():
    data = json.loads((Path(DATA)/'revision/comparison_map.json').read_text())
    rows = {row['reference_key']: row for row in data['rows']}
    fig = plt.figure(figsize=(W*MM, FIG_H*MM))
    # Panels share vertical space in their row and keep the type at its native print size.
    panels = [(1.5, .487, .510, 73, channel), (82.5, .487, .510, 73, flat_plate),
              (1.5, .005, .464, 67, speed_bump), (82.5, .005, .464, 67, expansions)]
    for i, (group, (x, bottom, height, units, draw)) in enumerate(zip(data['figure_panels'], panels)):
        ax = fig.add_axes([x/W, bottom, PANEL_W/W, height])
        ax.set(xlim=(0, PANEL_W), ylim=(units, 0))
        ax.axis('off')
        tag = 'abcd'[i]
        panel_heading(fig, tag, group['title'], left=x-1.5, top=0 if i < 2 else 67.6)
        geometry(ax, tag)
        draw(ax, *(rows[key] for key in group['studies']))
    save(fig, 'fig2_record')
    plotted = {key: data[key] for key in ('purpose', 'blank_meaning', 'figure_panels', 'rows')}
    (Path(RES)/'fig2_values.json').write_text(json.dumps(plotted, indent=2, ensure_ascii=False)+'\n')


if __name__ == '__main__':
    main()
