#!/usr/bin/env python3
"""Read the three-mesh series at the bump station x/L = -0.4 from the embedded panels of arXiv:2305.02540v3.

Usage: python3 -I code/read_bump_grid_series.py /path/to/2305.02540v3.pdf [--write]

The PDF is third-party material and is not part of this repository. The script checks its SHA-256, extracts the
native raster panels with poppler's pdfimages (no resampling), and reads

  * Fig. 10(a,b,c), skin friction along the bump with the dynamic Smagorinsky closure on the coarse, medium and fine
    meshes: the two model traces and the linear interpolation between the neighbouring measured stations at x/L = -0.4;
  * Fig. 12(a,b,c), mean streamwise velocity at x/L = -0.4 on the same three meshes: the two model traces at the heights
    of the particle-image measurements.

Panels are identified by PDF object number. Their positions on the page (left, centre, right in the top row) were
checked against the page layout; the captions of Figs 10 and 12 give coarse, medium and fine in that order.
With --write the readings replace data/revision/measurements/P31_Fig12{a,b,c}_DSM.csv and
P31_Fig10_friction_grid_series.json. Without it the script compares its readings with the stored files.
Requires numpy, scipy, Pillow and poppler-utils.
"""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage, signal

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/revision/measurements"
SHA256 = "cb427efb38bf00e0"          # first 16 hex digits of the archived arXiv v3 file
FRICTION = {"coarse": 552, "medium": 554, "fine": 556}      # Fig. 10(a,b,c), page 24
VELOCITY = {"coarse": 608, "medium": 609, "fine": 610}      # Fig. 12(a,b,c), page 26
STATION = -0.4


def extract(pdf, page, folder):
    """Native images of one page, keyed by PDF object number."""
    quiet = dict(stderr=subprocess.DEVNULL)      # poppler reports unreadable inline symbols on these pages; the panels are unaffected
    listing = subprocess.check_output(["pdfimages", "-list", "-f", str(page), "-l", str(page), str(pdf)], text=True, **quiet).splitlines()[2:]
    subprocess.run(["pdfimages", "-png", "-f", str(page), "-l", str(page), str(pdf), str(folder / f"p{page}")], check=True, **quiet)
    out = {}
    for line in listing:
        cell = line.split()
        if cell[10].isdigit():                   # inline images carry no object number
            out[int(cell[10])] = folder / f"p{page}-{int(cell[1]):03d}.png"
    return out


def native(path):
    return np.asarray(Image.open(path).convert("RGB"))


def runs(x):
    groups = np.split(x, np.flatnonzero(np.diff(x) > 1) + 1)
    return [(int(g[0]), int(g[-1])) for g in groups if len(g)]


def black(a):
    return (a[:, :, 0] == 0) & (a[:, :, 1] == 0) & (a[:, :, 2] == 0)


def colours(a):
    """Red: reinforcement-learning wall model. Blue: equilibrium wall model."""
    return [(a[:, :, 0] == 210) & (a[:, :, 1] == 0) & (a[:, :, 2] == 0),
            (a[:, :, 0] == 0) & (a[:, :, 1] == 127) & (a[:, :, 2] == 255)]


def friction(a):
    """10^3 C_f at the station: experiment (interpolated between its two neighbouring markers), learned, equilibrium."""
    xc = 293 + (STATION + 1) * (1751 - 293) / 2.5        # axis from x/L = -1 to 1.5
    rois = ndimage.find_objects(ndimage.label(black(a)[260:1250, 311:1730])[0])
    centres = []
    for r in rois:
        if r is None:
            continue
        yy, xx = r
        if xx.stop - xx.start == 22 and yy.stop - yy.start == 22:          # square experimental markers
            centres.append((311 + (xx.start + xx.stop - 1) / 2, 260 + (yy.start + yy.stop - 1) / 2))
    centres.sort()
    pts = np.array(centres)
    values = [np.interp(xc, *pts.T)]
    for m in colours(a):
        xs, ys = [], []
        for j in range(int(xc) - 35, int(xc) + 36):
            y = np.where(m[500:1100, j])[0] + 500
            if len(y):
                xs.append(j)
                ys.append(np.median(y))
        values.append(np.interp(xc, xs, ys))
    as_cf = lambda y: (1281 - y) / ((1281 - 229) / 20) - 5                  # axis from 10^3 C_f = -5 to 15
    near = [(round(-1 + (j - 293) * 2.5 / (1751 - 293), 4), round(as_cf(y), 3)) for j, y in pts if abs(j - xc) < 60]
    return [round(float(as_cf(v)), 3) for v in values], near


def measurements(panels):
    """Centres of the particle-image circles, which share native coordinates in the three panels."""
    stack = np.any([black(p) for p in panels], axis=0)
    ring = stack[1436:1463, 500:527]
    a = stack[110:1490, 455:1275].astype(float)
    t = ring.astype(float)
    v = signal.correlate(a, t, mode="valid", method="fft")
    count = signal.correlate(a, np.ones_like(t), mode="valid", method="fft")
    strength = v / np.sqrt(np.maximum(count, 1) * t.sum())
    coord = strength.argmax(axis=1) + 455 + 13
    peaks, _ = signal.find_peaks(strength.max(axis=1), distance=9, height=.53)
    found = []
    for j in peaks:
        y = j + 110 + 13
        if not 131 <= y <= 1463:
            continue
        x0 = coord[j]
        if y < 1250:
            b = np.where(stack[y, max(470, x0 - 27):x0 + 28])[0] + max(470, x0 - 27)
            if len(b) > 1:
                x0 = (b[0] + b[-1]) / 2
        found.append((y, x0))
    ref = np.asarray(found, dtype=float)
    ref[0, 1] = 2 * ref[1, 1] - ref[2, 1]      # the top circle touches the frame
    return ref


def solid_line(mask):
    """Centre of a model trace in each pixel row; a trace can be interrupted by the other model's ink."""
    b = mask.copy()
    b[:131] = False
    b[1491:] = False
    b[:, :470] = False
    b[:, 1361:] = False
    lab, _ = ndimage.label(b, structure=np.ones((3, 3), int))
    count = np.bincount(lab.ravel())
    count[0] = 0
    large = np.isin(lab, np.flatnonzero(count > 1000))
    y, x, fine = [], [], []
    for j, row in enumerate(large):
        if not np.any(row):
            continue
        centres = [(lo + hi) / 2 for lo, hi in runs(np.flatnonzero(row))]
        if len(centres) == 1:
            fine.append((j, centres[0]))
        y.append(j)
        x.append(centres)
    yy, xx = np.asarray(fine).T
    estimate = np.interp(y, yy, xx)
    xx = np.array([c[np.argmin(np.abs(np.asarray(c) - e))] for c, e in zip(x, estimate)])
    return np.array(y), xx


def velocity(panel, ref):
    scale = (1364 - 466) / .45                  # axis from u/U_inf = 0.55 to 1.00
    curves = [solid_line(c) for c in colours(panel)]
    low = max(yy[0] for yy, _ in curves)
    high = min(yy[-1] for yy, _ in curves)
    sel = ref[(ref[:, 0] >= low) & (ref[:, 0] <= high)]
    sy, sx = sel.T
    learned, equilibrium = [np.interp(sy, yy, xx) for yy, xx in curves]
    us = [(xx - 466) / scale + .55 for xx in (sx, learned, equilibrium)]
    ys = (1495 - sy) * .06 / (1495 - 127)       # axis from y/L = 0 to 0.06
    return np.asarray([sy, sx, ys, *us]).T


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    digest = hashlib.sha256(args.pdf.read_bytes()).hexdigest()
    assert digest.startswith(SHA256), f"not the archived arXiv v3 file: {digest[:16]}"
    header = "y_pixel,piv_x_pixel,y_over_L,PIV_U_over_Uinf,RLWM_DSM_U_over_Uinf,EQWM_DSM_U_over_Uinf"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        p24, p26 = extract(args.pdf, 24, tmp), extract(args.pdf, 26, tmp)
        series = {}
        for mesh, obj in FRICTION.items():
            (experiment, learned, equilibrium), near = friction(native(p24[obj]))
            series[mesh] = dict(pdf_object=obj, panel="Fig. 10(%s)" % "abc"[list(FRICTION).index(mesh)],
                                experiment_interpolated=experiment, learned=learned, equilibrium=equilibrium,
                                neighbouring_measured_stations=near)
        panels = {mesh: native(p26[obj]) for mesh, obj in VELOCITY.items()}
        ref = measurements(list(panels.values()))
        tables = {mesh: velocity(panel, ref) for mesh, panel in panels.items()}
    record = dict(
        source="Zhou and Bae, arXiv:2305.02540v3, Fig. 10(a,b,c), p. 24; dynamic Smagorinsky closure",
        pdf_sha256=digest, station_x_over_L=STATION, units="10^3 C_f",
        method="Native embedded panels extracted with pdfimages. Model traces: median ink row of each colour in the pixel columns "
               "within 35 px of the station. Experiment: linear interpolation between the two neighbouring square markers.",
        reading_precision=0.1,
        panel_identity="Object numbers 552, 554 and 556 are drawn left, centre and right in the top row of p. 24; the caption gives "
                       "(a,d) coarse, (b,e) medium and (c,f) fine, top row dynamic Smagorinsky.",
        meshes=series)
    if args.write:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "P31_Fig10_friction_grid_series.json").write_text(json.dumps(record, indent=1) + "\n")
        for mesh, table in tables.items():
            letter = "abc"[list(VELOCITY).index(mesh)]
            np.savetxt(OUT / f"P31_Fig12{letter}_DSM.csv", table, delimiter=",", fmt="%.7g", header=header, comments="")
    else:
        stored = json.loads((OUT / "P31_Fig10_friction_grid_series.json").read_text())
        assert stored["meshes"] == json.loads(json.dumps(series)), "friction readings differ from the stored file"
        for mesh, table in tables.items():
            letter = "abc"[list(VELOCITY).index(mesh)]
            kept = np.loadtxt(OUT / f"P31_Fig12{letter}_DSM.csv", delimiter=",", skiprows=1)
            assert kept.shape == table.shape and np.allclose(kept, table, rtol=1e-6, atol=1e-6), f"velocity readings differ: {mesh}"
        print("stored readings reproduced")
    for mesh in series:
        s = series[mesh]
        print(mesh, "10^3 Cf experiment/learned/equilibrium", s["experiment_interpolated"], s["learned"], s["equilibrium"],
              "velocity rows", len(tables[mesh]))


if __name__ == "__main__":
    main()
