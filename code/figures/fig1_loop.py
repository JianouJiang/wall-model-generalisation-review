#!/usr/bin/env python3
"""Research figure rendering from the accompanying public data."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, FancyBboxPatch
from style import *
(GRID, FILL, ACC) = ('#c9c8c2', '#f0efec', '#2a78d6')

def arrow(ax, p0, p1, color=INK, lw=0.9, rad=0.0, ms=7, ls='-', clip=True):
    a = FancyArrowPatch(p0, p1, arrowstyle='-|>', mutation_scale=ms, color=color, lw=lw, linestyle=ls, connectionstyle=f'arc3,rad={rad}', shrinkA=0, shrinkB=0, zorder=5)
    a.set_clip_on(clip)
    ax.add_patch(a)

def tag(ax, x, y, s):
    ax.text(x, y, s, ha='center', va='center', fontsize=FS, fontweight='bold', color='white', zorder=8, bbox=dict(boxstyle='circle,pad=0.2', fc=INK, ec='none'))

def panel_a(fig):
    ax = fig.add_axes([0.0, 0.0, 0.53, 1.0])
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 8.0)
    ax.axis('off')
    (x0, x1, yw, dy) = (0.55, 6.15, 1.5, 0.85)
    top = yw + 4 * dy
    ax.add_patch(Rectangle((x0, top), x1 - x0, 7.05 - top, fc=FILL, ec='none'))
    for k in range(1, 5):
        ax.plot([x0, x1], [yw + k * dy] * 2, color=GRID, lw=0.5, zorder=1)
    for xx in np.linspace(x0, x1, 5):
        ax.plot([xx, xx], [yw, top], color=GRID, lw=0.5, zorder=1)
    ax.add_patch(Rectangle((x0, yw - 0.3), x1 - x0, 0.3, fc='white', ec=MUTE, hatch='//////', lw=0.0, zorder=2))
    ax.plot([x0, x1], [yw, yw], color=INK, lw=1.0, zorder=3)
    ax.text(x0, yw - 0.62, 'wall', fontsize=FS, color=MUTE, va='center')
    h = yw + 2.5 * dy
    ax.plot([x0, x1], [h, h], color=INK, lw=0.6, ls=(0, (4, 3)), zorder=3)
    ax.text(x0 - 0.1, h, '$h$', ha='right', va='center', fontsize=9)
    ax.text(x0 - 0.1, yw, '0', ha='right', va='center', fontsize=FS)
    (xb, sc) = (0.95, 1.45)

    def prof(y):
        return sc * np.log(1 + 40 * (y - yw) / (4 * dy)) / np.log(41)
    yy = np.linspace(yw, top, 200)
    ax.plot([xb, xb], [yw, top], color=MUTE, lw=0.4, zorder=3)
    m = yy >= h
    ax.plot(xb + prof(yy[m]), yy[m], color=INK, lw=1.1, zorder=4)
    ax.plot(xb + prof(yy[~m]), yy[~m], color=INK, lw=1.1, ls=(0, (2, 2)), zorder=4)
    for yc in (h, yw + 3.5 * dy):
        arrow(ax, (xb, yc), (xb + prof(yc), yc), lw=0.6, ms=5)
    ax.plot(xb + prof(h), h, 'o', ms=3.6, color=ACC, zorder=7)
    ax.text(x0 + 0.45, 6.4, 'O', ha='center', va='center', fontsize=FS, fontweight='bold', color='white', zorder=8, bbox=dict(boxstyle='circle,pad=0.2', fc=MUTE, ec='none'))
    ax.text(x0 + 0.85, 6.4, 'outer solution\n(LES or RANS)', fontsize=FS, va='center', color=INK, linespacing=1.05)
    (bx0, bx1, by0, by1) = (7.45, 11.15, 2.25, 5.0)
    ax.add_patch(FancyBboxPatch((bx0, by0), bx1 - bx0, by1 - by0, boxstyle='round,pad=0.02,rounding_size=0.14', fc='white', ec=ACC, lw=1.1, zorder=4))
    ax.text((bx0 + bx1) / 2, by1 - 0.4, 'wall model', fontsize=FS, ha='center', va='center', fontweight='bold', zorder=6)
    ax.text((bx0 + bx1) / 2, by1 - 0.95, 'approximates', fontsize=FS, ha='center', va='center', zorder=6)
    ax.text((bx0 + bx1) / 2, by0 + 0.8, '$\\tau_w=\\tau(h)-h\\,\\mathrm{d}p/\\mathrm{d}x$' + '\n' + '$-\\rho\\int_0^h \\mathrm{D}u/\\mathrm{D}t\\;\\mathrm{d}y$', fontsize=FS, ha='center', va='center', zorder=6, linespacing=1.25)
    arrow(ax, (x1 + 0.05, h), (bx0 - 0.04, h), color=ACC, lw=1.1)
    ax.text((x1 + bx0) / 2, h + 0.3, 'inputs', fontsize=FS, ha='center', va='center')
    (xo, xi, yp) = ((bx0 + bx1) / 2, 5.2, yw - 0.85)
    ax.plot([xo, xo, xi], [by0 - 0.03, yp, yp], color=ACC, lw=1.1, zorder=5, solid_capstyle='butt')
    arrow(ax, (xi, yp), (xi, yw - 0.02), color=ACC, lw=1.1)
    ax.text(7.7, yp - 0.36, 'wall stress $\\tau_w$', fontsize=FS, ha='center', va='center')
    arrow(ax, (5.55, yw + 0.12), (5.55, h - 0.12), color=MUTE, lw=0.8, rad=-0.35, ms=6)
    tag(ax, 1.15, yp - 0.36, '1')
    ax.text(1.45, yp - 0.36, 'states it can return', fontsize=FS, va='center')
    xbr = 2.95
    ax.plot([xbr, xbr], [yw + 0.06, h - 0.06], color=INK, lw=0.7, zorder=6)
    for ye in (yw + 0.06, h - 0.06):
        ax.plot([xbr - 0.09, xbr + 0.09], [ye, ye], color=INK, lw=0.7, zorder=6)
    tag(ax, 3.22, yw + 1.275, '2')
    tag(ax, 7.5, 5.72, '3')
    ax.text(7.8, 5.72, 'information\nin the inputs', fontsize=FS, va='center', linespacing=1.0)
    ax.plot([7.3, 6.95], [5.55, h + 0.5], color=INK, lw=0.5, zorder=6)
    tag(ax, 7.5, 6.85, '4')
    ax.text(7.8, 6.85, 'coupling: where inputs\nare read, how $\\tau_w$ is applied', fontsize=FS, va='center', linespacing=1.0)
    tag(ax, xi - 0.45, yw - 0.6, '4')
    letter(fig, 0.008, 0.94, 'a', 'The coupled loop')

def panel_b(fig):
    ax = fig.add_axes([0.535, 0.25, 0.215, 0.53])
    eta = np.linspace(0, 1.28, 300)
    u = -1.2 * eta + 2.2 * eta ** 2
    ue = np.log(1 + 40 * eta) / np.log(41)
    assert abs(u[0]) < 1e-12 and abs(ue[0]) < 1e-12 and (abs(-1.2 + 2.2 - 1.0) < 1e-12)
    ax.fill_betweenx(eta, 0, u, where=u < 0, color=GRID, lw=0, zorder=1)
    ax.plot(u, eta, color=INK, lw=1.2, zorder=4)
    ax.plot(ue[eta <= 1.0], eta[eta <= 1.0], color=ACC, lw=1.1, ls=(0, (3, 2)), zorder=3)
    ax.axvline(0, color=MUTE, lw=0.4, zorder=2)
    ax.plot([-0.75, 1.0], [1.0, 1.0], color=INK, lw=0.6, ls=(0, (4, 3)), zorder=2)
    ax.plot(1.0, 1.0, 'o', ms=3.6, color=ACC, zorder=6)
    ax.add_patch(Rectangle((-0.75, -0.11), 2.9, 0.11, fc='white', ec=MUTE, hatch='//////', lw=0.0, zorder=2, clip_on=False))
    ax.plot([-0.75, 2.15], [0, 0], color=INK, lw=1.0, zorder=5, clip_on=False)
    ax.set_xlim(-1.75, 2.15)
    ax.set_ylim(0, 1.3)
    ax.axis('off')
    ax.text(-0.82, 1.0, '$h$', ha='right', va='center', fontsize=9)
    ax.text(-0.82, 0.0, '0', ha='right', va='center', fontsize=FS)
    ax.text(1.07, 0.93, '$u(h)>0$', fontsize=FS, va='top', ha='left', zorder=7)
    ax.text(-0.42, 0.42, 'reversed\nlayer', fontsize=FS, color=MUTE, va='center', ha='right', linespacing=1.0)
    ax.plot([-0.38, -0.1], [0.36, 0.2], color=MUTE, lw=0.5, zorder=6)
    for (yv, col, ls, p0, p1, lab) in ((-0.3, INK, '-', (0.0, -0.3), (-0.6, -0.3), 'flow: $\\tau_w<0$'), (-0.5, ACC, (0, (3, 2)), (-0.6, -0.5), (0.0, -0.5), 'law: $\\tau_w>0$')):
        arrow(ax, p0, p1, color=col, lw=1.0, ls=ls, clip=False)
        ax.text(0.16, yv, lab, fontsize=FS, ha='left', va='center', clip_on=False)
    letter(fig, 0.565, 0.94, 'b', 'Reversed layer')

def box(ax, x, y, w, h, s, ec=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.01,rounding_size=0.08', fc='white', ec=ec, lw=0.9, zorder=4))
    ax.text(x + w / 2, y + h / 2, s, fontsize=FS, ha='center', va='center', zorder=6, linespacing=1.0)

def panel_c(fig):
    ax = fig.add_axes([0.775, 0.0, 0.225, 1.0])
    ax.set_xlim(0, 4.5)
    ax.set_ylim(0, 8.0)
    ax.axis('off')
    ax.text(0.05, 6.85, 'Exact-input test', fontsize=FS, va='center', fontweight='bold')
    box(ax, 0.05, 5.4, 1.75, 1.0, 'reference\ndata')
    box(ax, 2.1, 5.4, 1.3, 1.0, 'wall\nmodel', ec=ACC)
    box(ax, 3.7, 5.4, 0.75, 1.0, '$\\tau_w$')
    arrow(ax, (1.82, 5.9), (2.07, 5.9))
    arrow(ax, (3.42, 5.9), (3.67, 5.9))
    ax.text(0.05, 4.45, 'map response to\nprescribed inputs;\nno solver feedback', fontsize=FS, color=MUTE, va='center', linespacing=1.05)
    ax.plot([0.05, 4.45], [3.55, 3.55], color=GRID, lw=0.6)
    ax.text(0.05, 3.05, 'Coupled test', fontsize=FS, va='center', fontweight='bold')
    box(ax, 0.05, 1.5, 1.45, 1.1, 'solver')
    box(ax, 3.0, 1.5, 1.45, 1.1, 'wall\nmodel', ec=ACC)
    arrow(ax, (1.55, 2.35), (2.97, 2.35), color=ACC)
    arrow(ax, (2.97, 1.75), (1.55, 1.75), color=ACC)
    ax.text(0.05, 0.8, 'map and feedback;\nerrors mixed with O', fontsize=FS, color=MUTE, va='center', linespacing=1.05)
    letter(fig, 0.785, 0.94, 'c', 'What each test sees')

def main():
    fig = plt.figure(figsize=(W * MM, 66 * MM))
    panel_a(fig)
    panel_b(fig)
    panel_c(fig)
    save(fig, 'fig1_loop')
if __name__ == '__main__':
    main()
