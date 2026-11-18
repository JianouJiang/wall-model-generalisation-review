#!/usr/bin/env python3
"""Agreement of two retrospective passes on the choices for a proposed test."""
import json
import sys
from itertools import product
from pathlib import Path

from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import BAND, BLUE, DATA, FS, G1, G2, INK, MM, MUTE, RES, W, panel_heading, plt, save

CHOICES = (('Cause', 'cause', 'same_cause'), ('Quantity class', 'observable_class', 'same_observable_class'),
           ('Factor to vary', 'factor_varied_alone', 'same_factor'))
BAR_BASE = 28.5
ROW_Y = (34.2, 40.7, 47.2)
ID_TOP = 53.4
HEIGHT = 64.5


def label(ax, x, y, text, *, align='left', color=INK):
    ax.text(x, y, text, ha=align, va='center', color=color, fontsize=FS)


def dot(ax, x, y, matched, color=INK):
    ax.plot(x, y, marker='o', linestyle='none', ms=4.8 if matched else 3.7,
            mfc=color if matched else 'white', mec=color if matched else G1, mew=.8, zorder=4)


def marginal_counts(ax, counts, total):
    left, zero = 3.5, 33.5
    label(ax, left, 18.2, f'Cases (of {total})')
    ax.plot([left, zero], [BAR_BASE]*2, color=G1, lw=.55)
    for tick in (0, 5, 10, total):
        x = zero - (zero-left)*tick/total
        ax.plot([x, x], [BAR_BASE-1.1, BAR_BASE], color=G1, lw=.55)
        label(ax, x, BAR_BASE-3.7, str(tick), align='center', color=MUTE)
    for (name, _, _), y in zip(CHOICES, ROW_Y):
        label(ax, 59.7, y, name, align='right')
        width = (zero-left)*counts[name]/total
        ax.add_patch(Rectangle((zero-width, y-1.55), width, 3.1, fc=G1, ec='none'))
        label(ax, zero-width-1.5, y, str(counts[name]), align='right')


def combinations(ax, patterns):
    # The count bar, the three decisions and the archived IDs share a column.
    first, spacing = 67.5, 12.35
    xs = [first + i*spacing for i in range(len(patterns))]
    for x, matched, text in ((124.0, True, 'Matched'), (142.0, False, 'Differed')):
        dot(ax, x, 2.9, matched)
        label(ax, x+2.4, 2.9, text)
    for degree, title in ((3, 'All three'), (2, 'Two choices'), (1, 'One choice'), (0, 'None')):
        group = [x for x, item in zip(xs, patterns) if sum(item['choices']) == degree]
        label(ax, (group[0]+group[-1])/2, 9.6, title, align='center')
        ax.plot([group[0]-4.7, group[-1]+4.7], [12.2, 12.2], lw=.55, color=G2)

    left, right = first-5.5, xs[-1]+5.5
    base, unit = BAR_BASE, 3.85
    ax.plot([left, right], [base]*2, color=G1, lw=.55, zorder=1)
    # A pale guide behind alternate rows preserves the association with the
    # choice labels at left, including columns with zero cases.
    for y in ROW_Y[::2]:
        ax.add_patch(Rectangle((left, y-2.7), right-left, 5.4, fc=BAND, ec='none', zorder=0))
    label(ax, 59.7, ID_TOP, 'Case IDs', align='right', color=MUTE)

    for x, item in zip(xs, patterns):
        flags, n = item['choices'], item['count']
        complete = all(flags)
        color = BLUE if complete else INK
        height = unit*n
        if n:
            ax.add_patch(Rectangle((x-2.2, base-height), 4.4, height,
                                   fc=BLUE if complete else G1, ec='none', zorder=2))
        label(ax, x, base-height-2.2, str(n), align='center')
        matched_y = [y for y, matched in zip(ROW_Y, flags) if matched]
        if len(matched_y) > 1:
            ax.plot([x, x], [matched_y[0], matched_y[-1]], color=color, lw=1, zorder=2)
        for y, matched in zip(ROW_Y, flags):
            dot(ax, x, y, matched, color)
        for i, case_id in enumerate(item['case_ids']):
            label(ax, x, ID_TOP + 4.1*i, case_id, align='center', color=MUTE)


def main():
    cases = json.loads((Path(DATA)/'checklist_cases.json').read_text())['cases']
    paired_rows = json.loads((Path(DATA)/'revision/checklist_choices.json').read_text())['cases']
    paired = {row['case']: row for row in paired_rows}
    assert len(paired_rows) == len(paired) == len(cases) == 13
    assert set(paired) == {case['case'] for case in cases}
    assert all(c['records'][p]['step5_from_the_item_record'] == 'unknown' for c in cases for p in 'AB')
    cases_by_pattern = {bits: [] for bits in product((False, True), repeat=len(CHOICES))}
    for case in cases:
        row = paired[case['case']]
        flags = tuple(row['A'][field] == row['B'][field] for _, field, _ in CHOICES)
        assert flags == tuple(case['agreement'][key] for _, _, key in CHOICES)
        cases_by_pattern[flags].append(case['case'])
    counts = {name: sum(len(ids) for bits, ids in cases_by_pattern.items() if bits[i])
              for i, (name, _, _) in enumerate(CHOICES)}
    counts['All three'] = len(cases_by_pattern[(True, True, True)])
    ordered = sorted(cases_by_pattern, key=lambda bits: (sum(bits), len(cases_by_pattern[bits]), bits),
                     reverse=True)
    patterns = [dict(choices=list(bits), count=len(cases_by_pattern[bits]), case_ids=cases_by_pattern[bits])
                for bits in ordered]

    fig = plt.figure(figsize=(W*MM, HEIGHT*MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, W), ylim=(HEIGHT, 0))
    ax.axis('off')
    panel_heading(fig, 'a', 'Agreement by choice')
    panel_heading(fig, 'b', 'Cases by combination of matches', left=60.7)
    marginal_counts(ax, counts, len(cases))
    combinations(ax, patterns)
    save(fig, 'fig4_checklist')

    result = dict(cases=len(cases), agreement=counts,
                  case_order=[dict(number=i+1, case=c['case'], agreement=c['agreement']) for i, c in enumerate(cases)],
                  agreement_patterns=[dict(choices=list(bits), count=len(ids))
                                      for bits, ids in sorted(cases_by_pattern.items()) if ids],
                  choice_order=[name for name, _, _ in CHOICES], display_patterns=patterns,
                  assurance='withheld in all 13 cases')
    (Path(RES)/'fig4_values.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
