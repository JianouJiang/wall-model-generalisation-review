#!/usr/bin/env python3
"""Re-read Chen and He, Fig. 25, at the labelled y+ = 100 tick."""
import argparse
import hashlib
import json
from pathlib import Path

from verify_fig3_source import vertical_coordinate


def centre(rectangle):
    return (rectangle.x0 + rectangle.x1) / 2, (rectangle.y0 + rectangle.y1) / 2


def verify(pdf):
    import fitz

    root = Path(__file__).resolve().parents[1]
    support = json.loads((root / "data/revision/claim_support.json").read_text())
    record = next(row["profile_reading"] for row in support
                  if row["claim_id"] == "Chen2023-source-coupling")
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != record["pdf_sha256"]:
        raise ValueError("Use the specified Cambridge or Oxford archive PDF for this coordinate extraction.")
    with fitz.open(pdf) as document:
        paths = document[record["page"] - 1].get_drawings()
    indices = record["pdf_path_indices"]
    x = paths[indices["x_100"]]["rect"].x0
    zero = paths[indices["vertical_zero"]]["rect"].y0
    top = paths[indices["vertical_25"]]["rect"].y0
    units_per_point = 25 / (zero - top)
    dns = paths[indices["dns"]]
    uncoupled = paths[indices["uncoupled"]]
    markers = [paths[index] for index in indices["coupled_bracketing_markers"]]
    if dns["color"] != (0, 0, 0) or uncoupled["color"] != (1, 0, 0):
        raise ValueError("Reference or uncoupled path does not match the figure legend.")
    if any(marker["color"] != (0, 0, 1) or marker["items"][0][0] != "re" for marker in markers):
        raise ValueError("Coupled profile markers do not match the blue squares in the figure.")
    (left, y_left), (right, y_right) = [centre(marker["rect"]) for marker in markers]
    if not left < x < right:
        raise ValueError("The two source markers must bracket the labelled tick.")
    y_coupled = y_left + (x - left) * (y_right - y_left) / (right - left)
    ordinates = {"uncoupled": vertical_coordinate(uncoupled, x),
                 "coupled": y_coupled, "dns": vertical_coordinate(dns, x)}
    velocity = {name: (zero - y) * units_per_point for name, y in ordinates.items()}
    rounded = {name: round(value, 1) for name, value in velocity.items()}
    if rounded != record["u_plus"]:
        raise ValueError(f"Re-extracted U+ differs from the source record: {rounded}")
    stroke_width = dns["width"] * units_per_point
    if abs(velocity["coupled"] - velocity["dns"]) >= stroke_width:
        raise ValueError("The coupled–DNS difference exceeds the plotted reference stroke.")
    print(f"At y+ = {record['y_plus']}, U+ = {rounded}. DNS stroke width is {stroke_width:.2f} U+.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Chen and He (2023), JFM 955 A5, version of record")
    verify(parser.parse_args().pdf)
