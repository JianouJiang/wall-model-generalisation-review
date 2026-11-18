#!/usr/bin/env python3
"""Research figure rendering from the accompanying public data."""
import numpy as np
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.text as mtext
from matplotlib.path import Path
from matplotlib.transforms import Bbox
TOL = 1.0

def _visible_texts(fig):
    return [t for t in fig.findobj(mtext.Text) if t.get_visible() and t.get_text().strip() and (t.get_figure() is fig)]

def _poly(t, renderer, fig, shrink_px):
    bb = t.get_window_extent(renderer)
    rot = float(t.get_rotation()) % 180.0
    if abs(rot) < 1e-06:
        (x0, y0, x1, y1) = (bb.x0 + shrink_px, bb.y0 + shrink_px, bb.x1 - shrink_px, bb.y1 - shrink_px)
        if x1 <= x0 or y1 <= y0:
            x0 = x1 = (bb.x0 + bb.x1) / 2
            y0 = y1 = (bb.y0 + bb.y1) / 2
        return np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]])
    tmp = mtext.Text(0, 0, t.get_text(), fontproperties=t.get_fontproperties(), linespacing=t._linespacing)
    tmp.set_figure(fig)
    b0 = tmp.get_window_extent(renderer)
    (w, h) = (max(b0.width - 2 * shrink_px, 0.5), max(b0.height - 2 * shrink_px, 0.5))
    (cx, cy) = ((bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2)
    a = np.deg2rad(float(t.get_rotation()))
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    c = np.array([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2], [-w / 2, -h / 2]])
    return c @ R.T + [cx, cy]

def _desc(a):
    s = type(a).__name__
    lab = a.get_label() if hasattr(a, 'get_label') else ''
    if lab and (not lab.startswith('_')):
        s += f" '{lab}'"
    try:
        if isinstance(a, mlines.Line2D):
            xy = a.get_xydata()
            s += f' {np.round(xy[0], 2).tolist()}..{np.round(xy[-1], 2).tolist()}'
        elif isinstance(a, mpatches.Patch):
            e = a.get_extents()
            s += f' extent px {[round(v) for v in (e.x0, e.y0, e.x1, e.y1)]}'
    except Exception:
        pass
    return s

def _vertices(path):
    v = path.vertices
    if path.codes is None:
        return v
    keep = (path.codes != Path.CLOSEPOLY) & (path.codes != Path.STOP)
    return v[keep]

def _meet(a, closed_poly):
    if a.intersects_path(closed_poly, filled=False):
        return True
    v = _vertices(a)
    return bool(len(v)) and bool(closed_poly.contains_points(v).any())

def _alpha(c, a):
    import matplotlib.colors as mc
    try:
        return mc.to_rgba(c, a)[3]
    except (ValueError, TypeError):
        return 1.0

def layout(fig, tol_pt=TOL):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    px = fig.dpi / 72.0
    shrink = tol_pt * px
    (W, H) = (fig.bbox.width, fig.bbox.height)
    texts = _visible_texts(fig)
    polys = {id(t): _poly(t, r, fig, shrink) for t in texts}
    own_boxes = {id(t.get_bbox_patch()) for t in texts if t.get_bbox_patch() is not None}
    backs = {id(fig.patch)} | {id(ax.patch) for ax in fig.axes}
    hidden_axes = {id(ax) for ax in fig.axes if not ax.axison}

    def shown(a):
        if not a.get_visible() or a.get_figure() is not fig:
            return False
        if a.get_alpha() is not None and a.get_alpha() == 0:
            return False
        if type(a).__name__ == 'Spine' and (a.axes is None or id(a.axes) in hidden_axes):
            return False
        return True
    lines = [l for l in fig.findobj(mlines.Line2D) if shown(l) and _alpha(l.get_color(), l.get_alpha()) > 0]
    patches = [p for p in fig.findobj(mpatches.Patch) if shown(p) and id(p) not in backs and (id(p) not in own_boxes)]
    (clipped, crossings, overlaps) = ([], [], [])
    for t in texts:
        P = polys[id(t)]
        label = t.get_text().replace('\n', ' ')[:48]
        gid = t.get_gid() or ''
        if P[:, 0].min() < -0.5 or P[:, 0].max() > W + 0.5 or P[:, 1].min() < -0.5 or (P[:, 1].max() > H + 0.5):
            clipped.append(dict(text=label, gid=gid, extent_px=[round(v, 1) for v in (P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max())], figure_px=[round(W, 1), round(H, 1)]))
        tp = Path(P, closed=True)
        for l in lines:
            ls = l.get_linestyle()
            if ls not in ('None', '', ' ', 'none') and l.get_linewidth() > 0 and (len(l.get_xydata()) >= 2):
                path = l.get_transform().transform_path(l.get_path())
                if _meet(path, tp):
                    crossings.append(dict(text=label, gid=gid, other='line: ' + _desc(l)))
            if l.get_marker() not in (None, 'None', '', ' ', 'none') and l.get_markersize() > 0:
                half = l.get_markersize() * px / 2
                pts = l.get_transform().transform(l.get_xydata())
                for (x, y) in pts:
                    mp = Path([[x - half, y - half], [x + half, y - half], [x + half, y + half], [x - half, y + half], [x - half, y - half]], closed=True)
                    if _meet(mp, tp) or _meet(tp, mp):
                        crossings.append(dict(text=label, gid=gid, other=f'mark of {_desc(l)} at px {[round(x), round(y)]}'))
                        break
        for p in patches:
            (ec, fc) = (p.get_edgecolor(), p.get_facecolor())
            edge = p.get_linewidth() > 0 and ec[3] > 0
            face = p.get_fill() and fc[3] > 0
            if not (edge or face) and (not p.get_hatch()):
                continue
            path = p.get_transform().transform_path(p.get_path())
            if isinstance(p, mpatches.FancyArrowPatch):
                hit = _meet(path, tp)
            else:
                v = _vertices(path)
                hit = path.intersects_path(tp, filled=False) or (len(v) > 0 and bool(tp.contains_points(v).all()))
            if hit:
                crossings.append(dict(text=label, gid=gid, other='patch edge: ' + _desc(p)))
    for (i, a) in enumerate(texts):
        for b in texts[i + 1:]:
            (pa, pb) = (Path(polys[id(a)], closed=True), Path(polys[id(b)], closed=True))
            if _meet(pa, pb) or _meet(pb, pa):
                overlaps.append(dict(text=a.get_text().replace('\n', ' ')[:48], gid=a.get_gid() or '', other=b.get_text().replace('\n', ' ')[:48]))
    return dict(texts=len(texts), tolerance_pt=tol_pt, clipped=clipped, crossings=crossings, text_overlaps=overlaps)
