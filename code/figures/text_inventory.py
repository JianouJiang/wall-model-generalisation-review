#!/usr/bin/env python3
"""Research figure rendering from the accompanying public data."""
import json
import matplotlib.colors as mcolors

def dump(fig, path, name, width_mm=160):
    rows = []
    fig.canvas.draw()

    def add(t, where, role):
        s = t.get_text()
        if not s.strip() or not t.get_visible():
            return
        rows.append(dict(text=s, size_pt=round(float(t.get_fontsize()), 2), weight=str(t.get_fontweight()), rotation=round(float(t.get_rotation()), 1), colour=mcolors.to_hex(t.get_color()), where=where, role=role, math='$' in s))
    for (i, a) in enumerate(fig.axes):
        for t in a.texts:
            add(t, f'axes {i}', 'text')
        if a.axison:
            add(a.xaxis.label, f'axes {i}', 'axis label')
            add(a.yaxis.label, f'axes {i}', 'axis label')
            add(a.title, f'axes {i}', 'title')
            add(a._left_title, f'axes {i}', 'title')
            add(a._right_title, f'axes {i}', 'title')
            for axis in (a.xaxis, a.yaxis):
                (lo, hi) = sorted(axis.get_view_interval())
                for tick in axis.get_major_ticks():
                    if lo - 1e-09 <= tick.get_loc() <= hi + 1e-09:
                        add(tick.label1, f'axes {i}', 'tick label')
        leg = a.get_legend()
        if leg is not None:
            for t in leg.get_texts():
                add(t, f'axes {i}', 'legend')
    for t in fig.texts:
        add(t, 'figure', 'text')
    json.dump(dict(figure=name, width_mm=width_mm, texts=len(rows), rows=rows), open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    return rows
