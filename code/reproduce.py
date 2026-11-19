#!/usr/bin/env python3
"""Reproduce current figures; add --historical for superseded coding diagnostics."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--historical',action='store_true')
    args=parser.parse_args()
    # derive_memberships.py recomputes every fact-derived membership; check_agreement.py recomputes the agreement statistics and decisions.
    # derive_outcomes.py derives which treatment is closer in every controlled comparison from the recorded rows;
    # outcome_structure.py regroups those outcomes (exclusive places, dependence on what a source reports, kind of flow);
    # worked_decisions.py recomputes the three worked comparisons; flow_counts.py counts the stages of Box 1;
    # write_protocol.py writes docs/protocol.md and docs/contributing-reports.md from the same files.
    # Figure 4 and the Box 1 diagram are drawn from their output.
    scripts = (['analyse_scope.py', 'analyse_revision.py'] if args.historical else []) + ['derive_memberships.py', 'check_agreement.py',
        'summarise_comparisons.py', 'resolve_directions.py', 'derive_outcomes.py', 'outcome_structure.py', 'worked_decisions.py',
        'flow_counts.py', 'write_protocol.py'] + [f'figures/{name}.py' for name in ('fig1_loop', 'fig2_record', 'fig3_contrast', 'fig4_outcomes', 'box1_flow')]
    for script in scripts:
        subprocess.run([sys.executable, '-I', str(ROOT / 'code' / script)], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
