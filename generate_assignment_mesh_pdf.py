"""Generate a PDF plot for the three assignment mesh domains without third-party deps."""
from __future__ import annotations

from generate_assignment_mesh_svg import (
    mesh_by_grid,
    shape_l_fd,
    shape_pentagon_fd,
    shape_halfdisk_fd,
)


def pdf_escape(text: str) -> str:
    return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def build_pdf(content: str, width: int, height: int) -> bytes:
    objects = []
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    objects.append("<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
        f"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )
    objects.append(f"<< /Length {len(content.encode('latin-1'))} >>\nstream\n{content}\nendstream")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(sum(len(part) for part in out))
        out.append(f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1"))

    xref_pos = sum(len(part) for part in out)
    out.append(f"xref\n0 {len(objects)+1}\n".encode("latin-1"))
    out.append(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.append(f"{off:010d} 00000 n \n".encode("latin-1"))
    out.append(
        (
            f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n"
        ).encode("latin-1")
    )
    return b"".join(out)


def main():
    configs = [
        (shape_l_fd, (-0.05, 2.05, -0.05, 2.05), 0.10, "L-shape"),
        (shape_pentagon_fd, (-1.35, 1.35, -1.35, 1.35), 0.09, "Pentagon with hole"),
        (shape_halfdisk_fd, (-1.30, 1.30, -1.30, 0.10), 0.08, "Half-disk with 2 holes"),
    ]
    meshes = [mesh_by_grid(fd, bbox, h) for fd, bbox, h, _ in configs]

    W, H = 1600, 540
    gap = 30
    panel_w = (W - 4 * gap) / 3
    panel_h = H - 100
    py = 60

    ops = []
    ops.append("1 1 1 rg 0 0 {0} {1} re f".format(W, H))
    ops.append("0 0 0 RG 0 0 0 rg")
    ops.append("BT /F1 22 Tf 430 505 Td (Triangular meshes for the three assignment domains) Tj ET")

    for idx, ((_, bbox, _, title), mesh) in enumerate(zip(configs, meshes)):
        px = gap + idx * (panel_w + gap)
        xmin, xmax, ymin, ymax = bbox

        def map_xy(x, y):
            sx = px + (x - xmin) / (xmax - xmin) * panel_w
            sy = py + (y - ymin) / (ymax - ymin) * panel_h
            return sx, sy

        ops.append(f"BT /F1 16 Tf {px + panel_w/2 - 70:.2f} 480 Td ({pdf_escape(title)}) Tj ET")

        edges = set()
        for a, b, c in mesh.tri:
            for u, v in ((a, b), (b, c), (c, a)):
                if u > v:
                    u, v = v, u
                edges.add((u, v))

        ops.append("0.2 w 0.12 0.47 0.71 RG")
        for u, v in edges:
            x1, y1 = map_xy(*mesh.pts[u])
            x2, y2 = map_xy(*mesh.pts[v])
            ops.append(f"{x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    content = "\n".join(ops)
    pdf_bytes = build_pdf(content, W, H)
    out = "assignment_meshes.pdf"
    with open(out, "wb") as f:
        f.write(pdf_bytes)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
