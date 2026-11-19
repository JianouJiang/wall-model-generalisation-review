#!/usr/bin/env python3
"""Order of the arms in the matched wall-treatment contrasts, and the paired choices of the retrospective pilot."""
import json
import sys
from pathlib import Path

from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import BLUE, DATA, FS, G1, G2, INK, MM, MUTE, PROJECT, RES, W, panel_heading, plt, save

H = 57.0
THEME_LABEL = dict(balance='Non-equilibrium terms', inputs='Inputs or history', location='Sampling location',
                   imposition='Imposition', law='Form of the law', learned='Trained law', parameter='Coefficient',
                   on_off='With or without law', resolution='Near-wall resolution', other='Other')
CATEGORIES = (('order changes', BLUE), ('one order', G2), ('nothing resolved', 'white'))
CHOICES = (('Cause', 'same_cause'), ('Quantity', 'same_observable_class'), ('Factor', 'same_factor'))


def label(ax, x, y, text, *, ha='left', color=INK, **kw):
    return ax.text(x, y, text, ha=ha, va='center', color=color, fontsize=FS, **kw)


def segments(ax, left, y, counts, scale, height=2.5):
    """One stacked bar; a count is printed inside a segment wide enough to hold it."""
    x = left
    for (name, colour), n in zip(CATEGORIES, counts):
        width = n * scale
        if n:
            ax.add_patch(Rectangle((x, y - height / 2), width, height, fc=colour, ec=G1 if colour == 'white' else 'none', lw=.5, zorder=2))
        x += width
    return x


def themes(ax, summary):
    """Panel a: pairs of arm 0 with another arm, by what distinguishes the two treatments."""
    pairs = summary['pairs']
    by_theme = summary['by_theme']
    order = sorted(by_theme, key=lambda t: (t == 'other', -by_theme[t]['pairs'], t))
    rows = [('All pairs', [pairs['by_category'].get(k, 0) + (pairs['by_category'].get('reference-dependent only', 0) if k == 'nothing resolved' else 0)
                           for k, _ in CATEGORIES])]
    for t in order:
        got = by_theme[t]['by_category']
        rows.append((THEME_LABEL[t], [got.get(k, 0) + (got.get('reference-dependent only', 0) if k == 'nothing resolved' else 0) for k, _ in CATEGORIES]))
    left, right, top = 38.5, 70.5, 15.3
    pitch = (H - top - 3.2) / len(rows)
    x = 1.3
    for name, colour in CATEGORIES:
        ax.add_patch(Rectangle((x, 8.9), 3.0, 2.5, fc=colour, ec=G1 if colour == 'white' else 'none', lw=.5))
        label(ax, x + 4.0, 10.15, name.capitalize())
        x += 4.0 + 1.5 * len(name) + 3.0
    values = []
    for i, (name, counts) in enumerate(rows):
        y = top + (i + .5) * pitch + (0 if i == 0 else 1.2)
        label(ax, left - 1.6, y, name, ha='right')
        end = segments(ax, left, y, counts, (right - left) / sum(counts))     # each bar shows the composition of its own pairs
        label(ax, end + 1.2, y, f'{counts[0]} of {sum(counts)}', color=MUTE if i else INK)
        values.append(dict(row=name, order_changes=counts[0], one_order=counts[1], nothing_resolved=counts[2]))
    ax.plot([left, left], [top - .6, H - 2.6], color=G1, lw=.55, zorder=3)
    return values


def places(ax, summary):
    """Panel b: the order in every contrast, and where it changes; the three places are not exclusive."""
    where, e1, e2 = summary['where_the_order_changes'], summary['e1'], summary['e2']
    n = summary['contrasts']
    left, right, top, pitch = 122.0, 143.0, 9.0, 3.9
    scale = (right - left) / n
    counts = [e1[k] for k, _ in CATEGORIES]
    y = top + .5 * pitch
    label(ax, left - 1.6, y, 'All contrasts', ha='right')
    end = segments(ax, left, y, counts, scale)
    label(ax, end + 1.2, y, f'{counts[0]} of {n}')
    rows = [('Within a profile', where['within a profile'], ''),
            ('Between conditions', where['between conditions'], ''),
            ('Between quantities', where['between quantities'], f"of {e2['contrasts_with_two_classes_under_a_shared_condition']}")]
    for i, (name, count, note) in enumerate(rows):
        y = top + (i + 1.5) * pitch + .8
        label(ax, left - 1.6, y, name, ha='right')
        ax.add_patch(Rectangle((left, y - 1.25), count * scale, 2.5, fc=BLUE, ec='none', zorder=2))
        label(ax, left + count * scale + 1.2, y, f'{count} {note}'.strip(), color=MUTE)
    ax.plot([left, left], [top - .3, top + 4 * pitch + 1.1], color=G1, lw=.55, zorder=3)
    return dict(all_contrasts=dict(order_changes=counts[0], one_order=counts[1], nothing_resolved=counts[2]),
                places=[dict(place=name, contrasts=count) for name, count, _ in rows])


def pilot(ax, cases):
    """Panel c: the 13 retrospective cases, grouped by shared source papers."""
    groups = []
    for case in cases:
        papers = {case['later'], *case['earlier']}
        hit = [g for g in groups if g['papers'] & papers]
        groups = [g for g in groups if g not in hit]
        groups.append(dict(papers=papers.union(*(g['papers'] for g in hit)), cases=[c for g in hit for c in g['cases']] + [case]))
    groups.sort(key=lambda g: (-len(g['cases']), g['cases'][0]['case']))
    left, top, pitch_x, pitch_y = 108.6, 36.6, 3.45, 4.0
    x, columns = left, []
    for g in groups:
        for case in g['cases']:
            columns.append((x, case, len(g['cases'])))
            x += pitch_x
        x += 1.0 if len(g['cases']) > 1 else 0
    for i, (name, key) in enumerate(CHOICES):
        y = top + (i + .5) * pitch_y
        label(ax, left - 3.0, y, name, ha='right')
        for cx, case, _ in columns:
            matched = case['agreement'][key]
            ax.plot(cx, y, marker='o', ls='none', ms=4.0 if matched else 3.2, mfc=INK if matched else 'white', mec=INK if matched else G1, mew=.8, zorder=4)
        label(ax, columns[-1][0] + 2.6, y, str(sum(c['agreement'][key] for _, c, _ in columns)))
    y_group = top - 2.0
    start = 0
    for g in groups:
        n = len(g['cases'])
        if n > 1:
            x0, x1 = columns[start][0] - 1.3, columns[start + n - 1][0] + 1.3
            ax.plot([x0, x0, x1, x1], [y_group + .9, y_group, y_group, y_group + .9], color=INK, lw=.7, zorder=3, solid_joinstyle='miter')
        start += n
    y_mark = top + 3 * pitch_y + 1.6
    for cx, case, _ in columns:
        if case['group'] == 'P':
            ax.add_patch(Rectangle((cx - 1.25, y_mark - .55), 2.5, 1.1, fc=BLUE, ec='none', zorder=3))
    y_key = y_mark + 5.0
    ax.plot([left - 14.0, left - 14.0, left - 10.2, left - 10.2], [y_key + .45, y_key - .45, y_key - .45, y_key + .45], color=INK, lw=.7)
    label(ax, left - 8.9, y_key, 'share a source paper')
    ax.add_patch(Rectangle((left + 22.0, y_key - .55), 2.5, 1.1, fc=BLUE, ec='none'))
    label(ax, left + 25.6, y_key, 'informed step 5')
    return dict(order=[c['case'] for _, c, _ in columns], groups=[[c['case'] for c in g['cases']] for g in groups],
                informed=[c['case'] for _, c, _ in columns if c['group'] == 'P'],
                matches={name: sum(c['agreement'][key] for _, c, _ in columns) for name, key in CHOICES})


def main():
    summary = json.loads((Path(PROJECT) / 'results/revision/contrast_outcomes_summary.json').read_text())
    collection = summary['summary']['collection']
    cases = json.loads((Path(DATA) / 'checklist_cases.json').read_text())['cases']
    assert len(cases) == 13
    fig = plt.figure(figsize=(W * MM, H * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, W), ylim=(H, 0))
    ax.axis('off')
    panel_heading(fig, 'a', f"Order of two wall treatments in {collection['pairs']['n']} matched pairs")
    panel_heading(fig, 'b', f"Where the order changes in {collection['contrasts']} contrasts", left=93.5)
    panel_heading(fig, 'c', 'Pilot: matching choices in 13 cases', left=93.5, top=27.0)
    ax.add_artist(Line2D([93.5, 159.0], [26.0, 26.0], color=G2, lw=.55))
    a = themes(ax, collection)
    b = places(ax, collection)
    c = pilot(ax, cases)
    save(fig, 'fig4_outcomes')
    (Path(RES) / 'fig4_values.json').write_text(json.dumps(dict(pairs_by_theme=a, contrasts=b, pilot=c), indent=2) + '\n')


if __name__ == '__main__':
    main()
