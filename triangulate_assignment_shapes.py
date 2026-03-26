#!/usr/bin/env python3
"""Triangulate three assignment domains with pygmsh and plot with matplotlib.

Domains:
1) L-shape
2) Pentagon with a circular hole
3) Half-disk with two circular holes

Outputs:
- assignment_meshes_pygmsh.png
- assignment_meshes_pygmsh.pdf
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np

try:
    import meshio
    import pygmsh
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency. Install with: pip install pygmsh meshio matplotlib"
    ) from exc


@dataclass
class TriMesh2D:
    points: np.ndarray
    triangles: np.ndarray


def _to_trimesh(mesh: meshio.Mesh) -> TriMesh2D:
    points2d = mesh.points[:, :2]
    if "triangle" not in mesh.cells_dict:
        raise ValueError("Expected triangular cells in generated mesh")
    tris = mesh.cells_dict["triangle"]
    return TriMesh2D(points=points2d, triangles=tris)


def l_shape_mesh(mesh_size: float = 0.12) -> TriMesh2D:
    # Unit square with top-right quadrant removed.
    poly = np.array(
        [
            [0.0, 0.0],
            [2.0, 0.0],
            [2.0, 1.0],
            [1.0, 1.0],
            [1.0, 2.0],
            [0.0, 2.0],
        ]
    )
    with pygmsh.geo.Geometry() as geom:
        geom.add_polygon(poly, mesh_size=mesh_size)
        mesh = geom.generate_mesh(dim=2)
    return _to_trimesh(mesh)


def pentagon_hole_mesh(mesh_size: float = 0.11) -> TriMesh2D:
    cx, cy, r = 0.0, 0.0, 1.55
    angles = np.linspace(math.pi / 2, math.pi / 2 + 2 * math.pi, 5, endpoint=False)
    outer = np.column_stack([cx + r * np.cos(angles), cy + r * np.sin(angles)])

    with pygmsh.geo.Geometry() as geom:
        outer_loop = geom.add_polygon(outer, mesh_size=mesh_size)
        hole_disk = geom.add_disk([0.15, -0.05], 0.42, 0.42, mesh_size=mesh_size)
        geom.boolean_difference(outer_loop, hole_disk)
        mesh = geom.generate_mesh(dim=2)
    return _to_trimesh(mesh)


def half_disk_two_holes_mesh(mesh_size: float = 0.09) -> TriMesh2D:
    # Create full disk, cut with lower half-plane, then remove two holes.
    with pygmsh.geo.Geometry() as geom:
        outer_disk = geom.add_disk([0.0, 0.0], 2.0, 2.0, mesh_size=mesh_size)

        # Large rectangle that keeps y >= 0 portion.
        clip = geom.add_polygon(
            [
                [-2.5, 0.0],
                [2.5, 0.0],
                [2.5, 2.5],
                [-2.5, 2.5],
            ],
            mesh_size=mesh_size,
        )
        half_disk = geom.boolean_intersection(outer_disk, clip)

        h1 = geom.add_disk([-0.8, 0.9], 0.35, 0.35, mesh_size=mesh_size)
        h2 = geom.add_disk([0.9, 0.75], 0.28, 0.28, mesh_size=mesh_size)
        geom.boolean_difference(half_disk, [h1, h2])

        mesh = geom.generate_mesh(dim=2)
    return _to_trimesh(mesh)


def plot_meshes(meshes: list[TriMesh2D], titles: list[str], out_png: Path, out_pdf: Path) -> None:
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.6), constrained_layout=True)

    for ax, m, title in zip(axs, meshes, titles):
        tri = mtri.Triangulation(m.points[:, 0], m.points[:, 1], m.triangles)
        ax.triplot(tri, color="#1f4e79", linewidth=0.6)
        ax.set_aspect("equal")
        ax.set_title(title)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_frame_on(False)

    fig.suptitle("Triangulations using pygmsh", fontsize=14)
    fig.savefig(out_png, dpi=240, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    out_png = Path("assignment_meshes_pygmsh.png")
    out_pdf = Path("assignment_meshes_pygmsh.pdf")

    meshes = [
        l_shape_mesh(),
        pentagon_hole_mesh(),
        half_disk_two_holes_mesh(),
    ]
    titles = [
        "(a) L-shape",
        "(b) Pentagon with hole",
        "(c) Half-disk with two holes",
    ]
    plot_meshes(meshes, titles, out_png=out_png, out_pdf=out_pdf)

    print(f"Wrote {out_png}")
    print(f"Wrote {out_pdf}")


if __name__ == "__main__":
    main()
