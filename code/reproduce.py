#!/usr/bin/env python3
"""Reproduce the public scope analysis and four baseline figures."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    scripts = ['analyse_scope.py'] + [f'figures/{name}.py' for name in
        ('fig1_loop', 'fig2_record', 'fig3_contrast', 'fig4_checklist')]
    for script in scripts:
        subprocess.run([sys.executable, '-I', str(ROOT / 'code' / script)], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
