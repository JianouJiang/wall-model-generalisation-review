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
    scripts = (['analyse_scope.py', 'analyse_revision.py'] if args.historical else []) + ['summarise_comparisons.py'] + [f'figures/{name}.py' for name in
        ('fig1_loop', 'fig2_record', 'fig3_contrast', 'fig4_checklist')]
    for script in scripts:
        subprocess.run([sys.executable, '-I', str(ROOT / 'code' / script)], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
