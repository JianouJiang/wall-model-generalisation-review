#!/usr/bin/env python3
"""Box 1: flow of records and reports through search, screening and eligibility, and the agreement of a second
data extraction for each count quoted in the paper. Stage names follow the PRISMA 2020 flow diagram."""
import json
import sys
from pathlib import Path

from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import BLUE, FS, G1, G2, INK, MM, MUTE, PROJECT, RES, W, panel_heading, plt, save

H = 65.0
REV = Path(PROJECT) / 'results/revision'


def n(value):
    return f'{value:,}'


def box(ax, x, y, w, h, label, count, accent=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=0.9', fc='white', ec=BLUE if accent else INK,
                                lw=1.1 if accent else .8, zorder=3))
    ax.text(x + w / 2, y + 3.45, label, ha='center', va='center', fontsize=FS, color=INK, linespacing=1.05, zorder=5)
    ax.text(x + w / 2, y + h - 2.0, count, ha='center', va='center', fontsize=FS, fontweight='bold', color=INK, zorder=5)


def arrow(ax, p0, p1, colour=INK, lw=.8, ms=6):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>', mutation_scale=ms, color=colour, lw=lw, shrinkA=0, shrinkB=0, zorder=4))


def flow(ax, f):
    """Panel a: six stages from left to right; what leaves the flow is written under each step."""
    ident, scr, ret, eli, inc = f['identification'], f['screening'], f['retrieval'], f['eligibility'], f['included']
    why = ret['not_retrieved_by_reason']
    stages = [('Records\nidentified', n(ident['records_identified'])), ('Records\nscreened', n(scr['records_screened'])),
              ('Reports\nsought', n(scr['reports_sought'])), ('Full texts\nobtained', n(ret['full_texts_obtained'])),
              ('Reports\nassessed', n(eli['reports_assessed'])), ('Eligible\nreports', n(inc['eligible_reports']))]
    leaves = [f"{n(ident['duplicates_removed'])} duplicates,\n{n(ident['removed_before_screening_total'])} not journal\narticles in English",
              f"{n(scr['records_excluded'])} excluded\non title and\nabstract",
              f"{n(ret['reports_not_retrieved'])} not retrieved:\n{n(why['no candidate route'])} no open copy,\n{why['access refused']} refused,\n{why['unusable retrieval']} unusable",
              f"{eli['not_in_english_set_aside']} not in English,\nnot assessed",
              f"{eli['excluded']} excluded,\n{eli['contested']} contested"]
    width, height, top = 19.6, 10.6, 6.6
    gap = (W - 2.0 - 6 * width) / 5
    xs = [1.0 + i * (width + gap) for i in range(6)]
    mid = top + height / 2
    for i, (x, (label, count)) in enumerate(zip(xs, stages)):
        box(ax, x, top, width, height, label, count, accent=i == 5)
    for i, text in enumerate(leaves):
        x0, x1 = xs[i] + width, xs[i + 1]
        arrow(ax, (x0, mid), (x1, mid))
        xm = (x0 + x1) / 2
        ax.add_artist(Line2D([xm, xm], [mid, top + height + 1.6], color=G1, lw=.6, zorder=2))
        ax.text(xm, top + height + 2.3, text, ha='center', va='top', fontsize=FS, color=MUTE, linespacing=1.08, zorder=5)
    return dict(stages=[dict(stage=a.replace('\n', ' '), count=int(b.replace(',', ''))) for a, b in stages],
                leaving=[t.replace('\n', ' ') for t in leaves])


def table(ax, f, top):
    """Panel b: the counts quoted in the paper, the size of the second extraction and its agreement with the first."""
    derived = json.loads((REV / 'derived_memberships.json').read_text())
    agreement = json.loads((Path(PROJECT) / 'data/revision/agreement_v2.json').read_text())
    outcome = json.loads((REV / 'contrast_outcomes_summary.json').read_text())
    stats, sample = agreement['statistics'], agreement['sample']
    fresh, pool_c, pool_t = stats['fresh_random_sample'], stats['constitutive_pool']['constitutive'], stats['transfer_pool']['has_transfer']
    s1, s2 = outcome['agreement']['statistics']['S1_contrast_category'], outcome['agreement']['statistics']['S2_direction_by_pair_and_class']
    groups, inc, eli = f['evidence_groups'], f['included'], f['eligibility']
    work = {w['study_id']: w for w in agreement['per_work']}
    same = sum(work[i]['first']['disposition'] == work[i]['second']['disposition'] for i in sample['fresh_random_sample'])
    kappa = lambda s: f"{s['kappa']:.2f} ({s['kappa_bootstrap_95'][0]:.2f})"
    rows = [('Report eligible', f"{inc['eligible_reports']} of {eli['reports_assessed']} reports",
             f"random {fresh['broad']['n']} of {len(sample['fresh_sample_frame'])} reports", f"{same} of {fresh['broad']['n']} agree"),
            ('Controlled comparison', f"{groups['controlled_comparison']['reports']} of {inc['eligible_reports']} reports",
             f"the same {fresh['broad']['n']} reports", kappa(fresh['broad'])),
            ('Assumption tested on reference data', f"{groups['assumption_on_reference_data']['reports']} reports",
             f"{pool_c['n']} candidate reports", kappa(pool_c)),
            ('Test outside the fitting data', f"{groups['test_outside_fitting_data']['reports']} reports, {groups['test_outside_fitting_data']['tests']} tests",
             f"{pool_t['n']} candidate reports", kappa(pool_t)),
            ('Closer treatment, per comparison', f"{groups['controlled_comparison']['comparisons']} comparisons",
             f"{s1['n']} comparisons", kappa(s1)),
            ('Closer treatment, per quantity class', '', f"{s2['n']} within those {s1['n']}", kappa(s2))]
    cols = (2.0, 66.0, 100.0, 137.0)
    head = ('Item extracted', 'In the collection', 'Second extraction', '$\\kappa$ (lower bound)')
    pitch = 3.75
    y = top + 1.9
    for x, text in zip(cols, head):
        ax.text(x, y, text, ha='left', va='center', fontsize=FS, color=MUTE)
    ax.add_artist(Line2D([1.0, W - 1.0], [y + pitch / 2 + .1] * 2, color=G1, lw=.6))
    for i, row in enumerate(rows):
        y = top + 1.9 + (i + 1) * pitch + .5
        for x, text in zip(cols, row):
            if text:
                ax.text(x, y, text, ha='left', va='center', fontsize=FS, color=INK)
        if i < len(rows) - 1:
            ax.add_artist(Line2D([1.0, W - 1.0], [y + pitch / 2] * 2, color=G2, lw=.4))
    return [dict(item=r[0], count=r[1], second_extraction=r[2], agreement=r[3]) for r in rows]


def main():
    f = json.loads((REV / 'flow_counts.json').read_text())
    fig = plt.figure(figsize=(W * MM, H * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, W), ylim=(H, 0))
    ax.axis('off')
    panel_heading(fig, 'a', 'Search, screening and eligibility')
    split = 31.6
    panel_heading(fig, 'b', 'Quoted counts and agreement of a second extraction', top=split)
    ax.add_artist(Line2D([1.0, W - 1.0], [split - .6] * 2, color=G2, lw=.55))
    a = flow(ax, f)
    b = table(ax, f, split + 5.0)
    save(fig, 'box1_flow')
    (Path(RES) / 'box1_values.json').write_text(json.dumps(dict(flow=a, table=b), indent=2) + '\n')


if __name__ == '__main__':
    main()
