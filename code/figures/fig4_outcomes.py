#!/usr/bin/env python3
"""Which of two wall treatments lies closer to the reference in the controlled comparisons, and the paired choices of the
retrospective use of the five questions."""
import json
import sys
from pathlib import Path

from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import BLUE, DATA, FS, G1, G2, INK, MM, MUTE, PROJECT, RES, W, panel_heading, plt, save

H = 67.5          # total height; panel c has a two-line key (operator, 19 Nov 2026)
H_A = 64.5        # panel a keeps its original row geometry
GROUP = '#e6e5e0' # band behind cases that share a source paper
LIGHT = '#a9cbf0'
# Row names in the vocabulary of wall-modelled LES (owner steer, 19 Nov 2026): what the two treatments of a pair differ in.
THEME_LABEL = dict(balance='Non-equilibrium terms', inputs='Wall-model inputs', location='Sampling height',
                   imposition='Stress imposition', law='Form of wall law', learned='Machine-learned model', parameter='Model coefficient',
                   on_off='Wall model vs no-slip', resolution='Near-wall resolution', other='Other')
# Exclusive outcomes of a pair or a comparison, in drawing order.
CATEGORIES = (('along one profile only', LIGHT), ('beyond one profile', BLUE), ('one order', G2), ('nothing resolved', 'white'))
LEGEND = (('along one profile', LIGHT), ('beyond one profile', BLUE), ('One always closer', G2), ('Nothing resolved', 'white'))
CHOICES = (('Cause', 'same_cause'), ('Quantity', 'same_observable_class'), ('Factor', 'same_factor'))


def label(ax, x, y, text, *, ha='left', color=INK, **kw):
    return ax.text(x, y, text, ha=ha, va='center', color=color, fontsize=FS, **kw)


def segments(ax, left, y, counts, scale, height=2.5):
    """One stacked bar of exclusive outcomes."""
    x = left
    for (name, colour), n in zip(CATEGORIES, counts):
        width = n * scale
        if n:
            ax.add_patch(Rectangle((x, y - height / 2), width, height, fc=colour, ec=G1 if colour == 'white' else 'none', lw=.5, zorder=2))
        x += width
    return x


def legend(ax, y=10.15):
    """One key for panels a and b: the two blues are the two kinds of change of order."""
    x = 1.3
    label(ax, x, y, 'Order changes')
    x += 22.6
    for i, (name, colour) in enumerate(LEGEND):
        ax.add_patch(Rectangle((x, y - 1.25), 3.0, 2.5, fc=colour, ec=G1 if colour == 'white' else 'none', lw=.5))
        t = label(ax, x + 4.0, y, name)
        x += 4.0 + 1.5 * len(name) + (5.5 if i == 1 else 3.0)


def themes(ax, structure):
    """Panel a: pairs of the first treatment with another, by what distinguishes the two."""
    split = structure['pairs_by_theme_exclusive']
    order = sorted((t for t in split if t != 'all pairs'), key=lambda t: (t == 'other', -split[t]['pairs'], t))
    rows = [('All pairs', [split['all pairs'][k] for k, _ in CATEGORIES])] + [(THEME_LABEL[t], [split[t][k] for k, _ in CATEGORIES]) for t in order]
    left, right, top = 38.5, 70.5, 14.3
    pitch = (H_A - top - 3.2) / len(rows)
    values = []
    for i, (name, counts) in enumerate(rows):
        y = top + (i + .5) * pitch + (0 if i == 0 else 1.2)
        label(ax, left - 1.6, y, name, ha='right')
        end = segments(ax, left, y, counts, (right - left) / sum(counts))     # each bar shows the composition of its own pairs
        label(ax, end + 1.2, y, f'{counts[0] + counts[1]} of {sum(counts)}', color=MUTE if i else INK)
        values.append(dict(row=name, order_changes=counts[0] + counts[1], along_one_profile_only=counts[0], beyond_one_profile=counts[1],
                           one_order=counts[2], nothing_resolved=counts[3]))
    ax.plot([left, left], [top - .6, H_A - 2.6], color=G1, lw=.55, zorder=3)
    return values


def places(ax, structure, summary):
    """Panel b: exclusive outcome of every comparison, the same by how many individual comparisons it resolves, and,
    on its own denominator, the comparisons whose order differs between two classes of quantity under one condition."""
    exclusive, e2 = structure['exclusive_outcome'], summary['e2']
    n = structure['contrasts']
    beyond = structure['beyond_one_profile']
    counts = [exclusive['along one profile only'], beyond, exclusive['one order'], exclusive['nothing resolved']]
    assert sum(counts) == n
    left, right, top, pitch = 122.5, 144.0, 13.4, 3.4
    y = top + .5 * pitch
    label(ax, left - 1.6, y, 'All comparisons', ha='right')
    end = segments(ax, left, y, counts, (right - left) / n)
    label(ax, end + 1.2, y, f'{counts[0] + counts[1]} of {n}')
    names = {'1-2': '1 or 2 resolved', '3-5': '3 to 5 resolved', '6-10': '6 to 10 resolved', 'more than 10': 'Over 10 resolved'}
    bins = []
    for i, b in enumerate(structure['by_resolved_comparisons']):
        y = top + (i + 1.5) * pitch + .9
        row = [b['along_one_profile_only'], b['beyond_one_profile'], b['one_order'], 0]
        assert sum(row) == b['contrasts']
        label(ax, left - 1.6, y, names[b['resolved_comparisons']], ha='right')
        end = segments(ax, left, y, row, (right - left) / b['contrasts'])
        label(ax, end + 1.2, y, f"{b['order_changes']} of {b['contrasts']}", color=MUTE)
        bins.append(dict(resolved_comparisons=b['resolved_comparisons'], contrasts=b['contrasts'], order_changes=b['order_changes'],
                         along_one_profile_only=row[0], beyond_one_profile=row[1], one_order=row[2]))
    ax.plot([left, left], [top - .3, top + 5.5 * pitch + .3], color=G1, lw=.55, zorder=3)
    # Set apart: another denominator.
    y = top + 6.5 * pitch + .7
    ax.add_artist(Line2D([95.0, 159.0], [y - 2.8, y - 2.8], color=G1, lw=.5, ls=(0, (2, 2))))
    differ, compared = e2['order_differs_between_quantities'], e2['contrasts_with_two_classes_under_a_shared_condition']
    label(ax, left - 1.6, y, 'Between quantities', ha='right')
    ax.add_patch(Rectangle((left, y - 1.25), right - left, 2.5, fc='white', ec=G1, lw=.5, zorder=2))
    ax.add_patch(Rectangle((left, y - 1.25), (right - left) * differ / compared, 2.5, fc=INK, ec='none', zorder=3))
    label(ax, right + 1.2, y, f'{differ} of {compared}')
    return dict(all_contrasts=dict(along_one_profile_only=counts[0], beyond_one_profile=counts[1], order_changes=counts[0] + counts[1],
                                   one_order=counts[2], nothing_resolved=counts[3]),
                by_resolved_comparisons=bins, between_quantities=dict(differ=differ, compared=compared))


def pilot(ax, cases):
    """Panel c: the 13 retrospective cases, grouped by shared source papers (grey bands), with an in-panel key."""
    groups = []
    for case in cases:
        papers = {case['later'], *case['earlier']}
        hit = [g for g in groups if g['papers'] & papers]
        groups = [g for g in groups if g not in hit]
        groups.append(dict(papers=papers.union(*(g['papers'] for g in hit)), cases=[c for g in hit for c in g['cases']] + [case]))
    groups.sort(key=lambda g: (-len(g['cases']), g['cases'][0]['case']))
    left, top, pitch_x, pitch_y = 108.6, 46.4, 3.3, 3.5
    x, columns = left, []
    for g in groups:
        for case in g['cases']:
            columns.append((x, case, len(g['cases'])))
            x += pitch_x
        x += 1.0 if len(g['cases']) > 1 else 0
    # Grey band behind each group of cases that share a source paper.
    start = 0
    for g in groups:
        n = len(g['cases'])
        if n > 1:
            x0, x1 = columns[start][0] - 1.5, columns[start + n - 1][0] + 1.5
            ax.add_patch(Rectangle((x0, top - .2), x1 - x0, 3 * pitch_y + .4, fc=GROUP, ec='none', zorder=1))
        start += n
    for i, (name, key) in enumerate(CHOICES):
        y = top + (i + .5) * pitch_y
        label(ax, left - 3.0, y, name, ha='right')
        for cx, case, _ in columns:
            matched = case['agreement'][key]
            ax.plot(cx, y, marker='o', ls='none', ms=4.0 if matched else 3.2, mfc=INK if matched else 'white', mec=INK if matched else G1, mew=.8, zorder=4)
        label(ax, columns[-1][0] + 2.6, y, str(sum(c['agreement'][key] for _, c, _ in columns)))
    y_mark = top + 3 * pitch_y + 1.2
    for cx, case, _ in columns:
        if case['group'] == 'P':
            ax.add_patch(Rectangle((cx - 1.25, y_mark - .55), 2.5, 1.1, fc=BLUE, ec='none', zorder=3))
    # Key, two lines, inside the panel.
    k0 = 95.0
    y1 = y_mark + 3.4
    ax.plot(k0 + 1.0, y1, marker='o', ls='none', ms=4.0, mfc=INK, mec=INK, mew=.8)
    label(ax, k0 + 3.0, y1, 'same first choice')
    ax.plot(k0 + 31.0, y1, marker='o', ls='none', ms=3.2, mfc='white', mec=G1, mew=.8)
    label(ax, k0 + 33.0, y1, 'different')
    y2 = y1 + 3.6
    ax.add_patch(Rectangle((k0, y2 - 1.2), 2.6, 2.4, fc=GROUP, ec='none'))
    label(ax, k0 + 3.6, y2, 'same source paper')
    ax.add_patch(Rectangle((k0 + 33.0, y2 - .55), 2.5, 1.1, fc=BLUE, ec='none'))
    label(ax, k0 + 36.6, y2, 'used for step 5')
    return dict(order=[c['case'] for _, c, _ in columns], groups=[[c['case'] for c in g['cases']] for g in groups],
                informed=[c['case'] for _, c, _ in columns if c['group'] == 'P'],
                matches={name: sum(c['agreement'][key] for _, c, _ in columns) for name, key in CHOICES})


def main():
    summary = json.loads((Path(PROJECT) / 'results/revision/contrast_outcomes_summary.json').read_text())
    structure = json.loads((Path(PROJECT) / 'results/revision/outcome_structure.json').read_text())
    collection = summary['summary']['collection']
    cases = json.loads((Path(DATA) / 'checklist_cases.json').read_text())['cases']
    assert len(cases) == 13 and structure['contrasts'] == collection['contrasts']
    fig = plt.figure(figsize=(W * MM, H * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, W), ylim=(H, 0))
    ax.axis('off')
    panel_heading(fig, 'a', f"Which treatment is closer, by what differs ({collection['pairs']['n']} pairs)")
    panel_heading(fig, 'b', f"The {collection['contrasts']} controlled comparisons", left=93.5)
    panel_heading(fig, 'c', 'Same first choice in two applications', left=93.5, top=39.8)
    ax.add_artist(Line2D([93.5, 159.0], [39.2, 39.2], color=G2, lw=.55))
    legend(ax)
    a = themes(ax, structure)
    b = places(ax, structure, collection)
    c = pilot(ax, cases)
    save(fig, 'fig4_outcomes')
    (Path(RES) / 'fig4_values.json').write_text(json.dumps(dict(pairs_by_theme=a, contrasts=b, pilot=c), indent=2) + '\n')


if __name__ == '__main__':
    main()
