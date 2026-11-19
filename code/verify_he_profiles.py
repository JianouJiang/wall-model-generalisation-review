"""Recompute He et al.'s archived natural-convection wall-profile errors.

Usage: python3 verify_he_profiles.py [NaturalConvection.zip]
Without a local zip, fetch the authors' public 1.5 MB dataset. Output is JSON.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

import numpy as np


PUBLIC_URL = 'https://edata.stfc.ac.uk/bitstreams/234b81f1-36ce-4c57-a320-dd691400a151/download'
ARCHIVE_SHA = 'c51a51d6006412fb8d74b3bb533494e21fc59fa209bfc5630ebcb4663788b6fb'
RUNS = {
    'standard': ('RANS/STFC_StandardKeps_twoScaleWF', 'RANS/STFC_StandardKeps_scalableWF', 'scalable'),
    'sst': ('RANS/STFC_KomgSST_twoScaleWF', 'RANS/STFC_KomgSST_allYplusWF', 'all_y_plus'),
}
WALLS = ('hotWall', 'coldWall', 'baffleLeft', 'baffleRight')


def length_weighted_rms(values, spacing):
    left = values[:-1]
    right = values[1:]
    integral = np.sum(spacing * (left**2 + left*right + right**2) / 3)
    return float(np.sqrt(integral/spacing.sum()))


def length_weighted_mae(errors, spacing):
    left = errors[:-1]
    right = errors[1:]
    averages = (abs(left) + abs(right))/2
    crosses = left*right < 0
    averages[crosses] = (left[crosses]**2 + right[crosses]**2)/(2*abs(right[crosses]-left[crosses]))
    return float(np.sum(spacing*averages) / spacing.sum())


def on_support(profiles, column, lo, hi, baseline):
    # Integrate exactly for the linear interpolants by including every data knot.
    nodes = [[lo, hi]] + [data[:, 0][(data[:, 0] > lo) & (data[:, 0] < hi)] for data in profiles]
    y = np.unique(np.concatenate(nodes))
    ref, first, second = [np.interp(y, a[:, 0], a[:, column]) for a in profiles]
    spacing = np.diff(y)
    denominator = length_weighted_rms(ref, spacing)
    results = {}
    for name, model in [('two_scale', first), (baseline, second)]:
        error = model-ref
        rms = length_weighted_rms(error, spacing)
        results[name] = {'rmse': rms, 'mae': length_weighted_mae(error, spacing),
                         'relative_L2_percent': 100*rms/denominator}
    return results


def read_walls(archive, closure="standard"):
    first,second,baseline = RUNS[closure]
    out = {}
    for wall in WALLS:
        paths = [f'NaturalConvection/{run}/{wall}.dat' for run in ('DNS', first, second)]
        raw = [archive.read(path) for path in paths]
        profiles = [np.loadtxt(io.BytesIO(data)) for data in raw]
        if not np.array_equal(profiles[1][:, 0], profiles[2][:, 0]):
            raise ValueError(f'Different RANS sampling on {wall}')
        if not all(a.shape[1] == 4 and np.isfinite(a).all() and np.all(np.diff(a[:, 0]) > 0) for a in profiles):
            raise ValueError(f'Unexpected profile shape, values or ordinate on {wall}')
        lo = max(a[0, 0] for a in profiles)
        hi = min(a[-1, 0] for a in profiles)
        trim = 0.05*(hi-lo)
        record = {'common_y_m': [lo, hi], f'count_DNS_twoScale_{baseline}': [len(a) for a in profiles],
                  'data_file_sha256': {p: hashlib.sha256(a).hexdigest() for p, a in zip(paths, raw)},
                  'quantities': {}}
        for column, name in ((3, 'tau_w_Pa'), (2, 'q_w_W_per_m2')):
            node_y = profiles[1][:, 0]
            ref = np.interp(node_y, profiles[0][:, 0], profiles[0][:, column])
            err1 = abs(profiles[1][:, column] - ref)
            err2 = abs(profiles[2][:, column] - ref)
            record['quantities'][name] = {
                'full': on_support(profiles, column, lo, hi, baseline),
                'trimmed_5pct_each_end': on_support(profiles, column, lo+trim, hi-trim, baseline),
                'local_lower_abs_error_at_RANS_nodes': {
                    'two_scale': int(sum(err1 < err2)), baseline: int(sum(err1 > err2)), 'tie': int(sum(err1 == err2))}}
        out[wall] = record
    return out


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('archive', type=Path, nargs='?')
    cli.add_argument('--closure', choices=RUNS, default='standard')
    args = cli.parse_args()
    data = args.archive.read_bytes() if args.archive else urlopen(PUBLIC_URL, timeout=30).read(3_000_000)
    if hashlib.sha256(data).hexdigest() != ARCHIVE_SHA:
        raise ValueError('NaturalConvection.zip differs from the archived source identified in the report')
    with ZipFile(io.BytesIO(data)) as z:
        print(json.dumps(read_walls(z,args.closure), indent=2))
