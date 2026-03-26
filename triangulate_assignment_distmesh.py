#!/usr/bin/env python3
"""Triangulate assignment shapes using this repo's distmesh.py implementation."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from distmesh import (
    ddiff,
    dcircle,
    dintersect,
    dline,
    drectangle,
    distmesh2D,
    dunion,
    huniform,
)


def dconvex_polygon(p: np.ndarray, vertices: list[tuple[float, float]]) -> np.ndarray:
    d = np.full((p.shape[0],), -1.0e100)
    m = len(vertices)
    for i in range(m):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % m]
        d = np.maximum(d, dline(p, x1, y1, x2, y2))
    return d


def lshape_fd(p: np.ndarray) -> np.ndarray:
    return dunion(
        drectangle(p, 0.0, 1.0, 0.0, 2.0),
        drectangle(p, 0.0, 2.0, 0.0, 1.0),
    )


def pentagon_hole_fd(p: np.ndarray) -> np.ndarray:
    ang_out = np.deg2rad(90 + np.arange(5) * 72.0)  # CCW ordering
    outer = [(1.2 * math.cos(a), 1.2 * math.sin(a)) for a in ang_out]
    ang_in = np.deg2rad(90 + 36 + np.arange(5) * 72.0)  # rotated inner pentagon, CCW
    inner = [(0.38 * math.cos(a), 0.38 * math.sin(a)) for a in ang_in]
    return ddiff(dconvex_polygon(p, outer), dconvex_polygon(p, inner))


def halfdisk_two_holes_fd(p: np.ndarray) -> np.ndarray:
    d_half = dintersect(dcircle(p, 0.0, 0.0, 1.2), p[:, 1])  # lower half: y <= 0
    return ddiff(ddiff(d_half, dcircle(p, -0.55, -0.45, 0.23)), dcircle(p, 0.55, -0.45, 0.23))


def main() -> None:
    # Distmesh needs at least one fixed point because of nfix handling in distmesh.py.
    lshape_pfix = np.array([[0.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0], [1.0, 2.0], [0.0, 2.0]])
    pent_angles = np.deg2rad(90 + np.arange(5) * 72.0)
    pent_pfix = np.array([(1.2 * math.cos(a), 1.2 * math.sin(a)) for a in pent_angles])
    half_pfix = np.array([[-1.2, 0.0], [1.2, 0.0], [0.0, -1.2]])

    cases = [
        ("(a) L-shape", lshape_fd, huniform, 0.10, [-0.05, 2.05, -0.05, 2.05], lshape_pfix),
        ("(b) Pentagon with hole", pentagon_hole_fd, huniform, 0.09, [-1.35, 1.35, -1.35, 1.35], pent_pfix),
        ("(c) Half-disk with two holes", halfdisk_two_holes_fd, huniform, 0.08, [-1.30, 1.30, -1.30, 0.10], half_pfix),
    ]

    fig, axs = plt.subplots(1, 3, figsize=(14, 4.6), constrained_layout=True)
    for ax, (title, fd, fh, h0, bbox, pfix) in zip(axs, cases):
        plt.sca(ax)
        pts, tri = distmesh2D(fd, fh, h0, bbox, pfix)
        ax.clear()
        if tri.size == 0:
            ax.text(0.5, 0.5, "No triangles generated", ha="center", va="center", transform=ax.transAxes)
        else:
            ax.triplot(pts[:, 0], pts[:, 1], tri, color="#1f4e79", linewidth=0.6)
        ax.set_aspect("equal")
        ax.set_title(title)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_frame_on(False)

    fig.suptitle("Triangulations using distmesh.py", fontsize=14)
    out_png = Path("assignment_meshes_distmesh.png")
    out_pdf = Path("assignment_meshes_distmesh.pdf")
    fig.savefig(out_png, dpi=240, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    print(f"Wrote {out_png}")
    print(f"Wrote {out_pdf}")


if __name__ == "__main__":
    main()
