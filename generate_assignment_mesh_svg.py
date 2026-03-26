"""Generate an SVG plot of meshes for the three assignment shapes without third-party deps."""
from __future__ import annotations
import math
from dataclasses import dataclass


# --- distmesh-style signed-distance primitives (adapted from distmesh.py) ---
def ddiff(d1: float, d2: float) -> float:
    return max(d1, -d2)


def dintersect(d1: float, d2: float) -> float:
    return max(d1, d2)


def dunion(d1: float, d2: float) -> float:
    return min(d1, d2)


def dcircle(x: float, y: float, xc: float, yc: float, r: float) -> float:
    return math.hypot(x - xc, y - yc) - r


def drectangle(x: float, y: float, x1: float, x2: float, y1: float, y2: float) -> float:
    d1 = min(-y1 + y, y2 - y)
    d2 = min(d1, -x1 + x)
    return -min(d2, x2 - x)


def dline(x: float, y: float, x1: float, y1: float, x2: float, y2: float) -> float:
    nx = y1 - y2
    ny = x2 - x1
    nn = math.hypot(nx, ny)
    return -((x - x1) * nx + (y - y1) * ny) / nn


def dconvex_polygon(x: float, y: float, vertices: list[tuple[float, float]]) -> float:
    d = -1e100
    m = len(vertices)
    for i in range(m):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % m]
        d = max(d, dline(x, y, x1, y1, x2, y2))
    return d


@dataclass
class Mesh:
    pts: list[tuple[float, float]]
    tri: list[tuple[int, int, int]]


def mesh_by_grid(fd, bbox, h) -> Mesh:
    xmin, xmax, ymin, ymax = bbox
    nx = int((xmax - xmin) / h) + 1
    ny = int((ymax - ymin) / h) + 1

    grid = {}
    pts = []

    def point_idx(i, j):
        key = (i, j)
        if key in grid:
            return grid[key]
        x = xmin + i * h
        y = ymin + j * h
        idx = len(pts)
        pts.append((x, y))
        grid[key] = idx
        return idx

    tri = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            a = point_idx(i, j)
            b = point_idx(i + 1, j)
            c = point_idx(i + 1, j + 1)
            d = point_idx(i, j + 1)
            for t in ((a, b, c), (a, c, d)):
                cx = (pts[t[0]][0] + pts[t[1]][0] + pts[t[2]][0]) / 3.0
                cy = (pts[t[0]][1] + pts[t[1]][1] + pts[t[2]][1]) / 3.0
                if fd(cx, cy) <= 0.0:
                    tri.append(t)
    return Mesh(pts=pts, tri=tri)


def shape_l_fd(x, y):
    return dunion(drectangle(x, y, 0.0, 1.0, 0.0, 2.0), drectangle(x, y, 0.0, 2.0, 0.0, 1.0))


def shape_pentagon_fd(x, y):
    ang_out = [math.radians(a) for a in [90, 18, -54, -126, 162]]
    outer = [(1.2 * math.cos(a), 1.2 * math.sin(a)) for a in ang_out]
    ang_in = [math.radians(a + 30) for a in [90, 18, -54, -126, 162]]
    inner = [(0.38 * math.cos(a), 0.38 * math.sin(a)) for a in ang_in]
    return ddiff(dconvex_polygon(x, y, outer), dconvex_polygon(x, y, inner))


def shape_halfdisk_fd(x, y):
    d_half = dintersect(dcircle(x, y, 0.0, 0.0, 1.2), y)
    return ddiff(ddiff(d_half, dcircle(x, y, -0.55, -0.45, 0.23)), dcircle(x, y, 0.55, -0.45, 0.23))


def draw_mesh_panel(svg, mesh: Mesh, bbox, panel, title):
    px, py, pw, ph = panel
    xmin, xmax, ymin, ymax = bbox

    def map_xy(x, y):
        sx = px + (x - xmin) / (xmax - xmin) * pw
        sy = py + ph - (y - ymin) / (ymax - ymin) * ph
        return sx, sy

    svg.append(f'<text x="{px + pw/2:.1f}" y="{py-8:.1f}" text-anchor="middle" font-size="16">{title}</text>')
    for i, j, k in mesh.tri:
        x1, y1 = map_xy(*mesh.pts[i])
        x2, y2 = map_xy(*mesh.pts[j])
        x3, y3 = map_xy(*mesh.pts[k])
        svg.append(
            f'<polygon points="{x1:.2f},{y1:.2f} {x2:.2f},{y2:.2f} {x3:.2f},{y3:.2f}" '
            f'style="fill:none;stroke:#1f77b4;stroke-width:0.35" />'
        )


def main():
    configs = [
        (shape_l_fd, (-0.05, 2.05, -0.05, 2.05), 0.10, "L-shape"),
        (shape_pentagon_fd, (-1.35, 1.35, -1.35, 1.35), 0.09, "Pentagon with hole"),
        (shape_halfdisk_fd, (-1.30, 1.30, -1.30, 0.10), 0.08, "Half-disk with 2 holes"),
    ]

    meshes = [mesh_by_grid(fd, bbox, h) for fd, bbox, h, _ in configs]

    W, H = 1600, 520
    gap = 30
    panel_w = (W - 4 * gap) / 3
    panel_h = H - 80

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    svg.append('<rect width="100%" height="100%" fill="white"/>')
    svg.append('<text x="800" y="30" text-anchor="middle" font-size="22" font-weight="bold">Triangular meshes for the three assignment domains</text>')

    for idx, ((_, bbox, _, title), mesh) in enumerate(zip(configs, meshes)):
        px = gap + idx * (panel_w + gap)
        py = 60
        draw_mesh_panel(svg, mesh, bbox, (px, py, panel_w, panel_h), title)

    svg.append('</svg>')

    out = "assignment_meshes.svg"
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
