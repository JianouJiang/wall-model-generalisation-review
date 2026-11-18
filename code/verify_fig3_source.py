#!/usr/bin/env python3
"""Verify the 24 Figure 3b readings against the published Figure 9 PDF (requires PyMuPDF)."""
import argparse
import hashlib
import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parents[1]/'data/revision/outer_input_error.json'


def vertical_coordinate(stroke, x):
    matches = []
    for segment in stroke['items']:
        if segment[0] != 'l':
            continue
        a, b = segment[1:]
        if min(a.x, b.x) <= x < max(a.x, b.x):
            matches.append(a.y + (b.y-a.y)*(x-a.x)/(b.x-a.x))
    if len(matches) != 1:
        raise ValueError(f'Expected one line intersection at x = {x:.3f} pt, found {len(matches)}.')
    return matches[0]


def verify(source):
    import fitz

    record = json.loads(DATA.read_text())['station_readings']
    with fitz.open(source) as document:
        strokes = document[record['source_pdf_page']-1].get_drawings()
    readings = 0
    for row in record['series']:
        c = record['calibration'][row['source_panel']]
        xs = [strokes[i]['rect'].x0 for i in c['station_tick_strokes']]
        y1 = strokes[c['one_percent_tick_stroke']]['rect'].y0
        y10 = strokes[c['ten_percent_tick_stroke']]['rect'].y0
        expected_ticks = [*c['station_x_pt'], c['y_at_1_percent_pt'], c['y_at_10_percent_pt']]
        measured_ticks = [*xs, y1, y10]
        if not all(math.isclose(x, y, abs_tol=.002) for x, y in zip(measured_ticks, expected_ticks)):
            raise ValueError(f"Axis calibration differs in Fig. 9({row['source_panel']}).")
        stroke = strokes[row['source_stroke_index']]
        for i, x in enumerate(xs):
            y = vertical_coordinate(stroke, x)
            value = 10**((y1-y)/(y1-y10))
            if abs(y-row['y_pt'][i])>.002 or float(f'{value:.2g}') != row['error_percent_approx'][i]:
                raise ValueError(f"{row['outer_closure']} / {row['wall_model']} differs at Re_x = {record['re_x'][i]}.")
            readings += 1
    print(f'{readings} local error readings verified against the source curves.')
    print('Supplied PDF SHA256', hashlib.sha256(source.read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path, help='Lozano-Durán and Bae (2023), JFM 963 A35, version of record')
    verify(parser.parse_args().pdf)
