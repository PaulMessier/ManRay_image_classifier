"""Exact-coordinate thumbnail atlas and evidence-qualified semantic legend."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import fitz
import numpy as np
import pandas as pd
from PIL import Image, ImageOps

from pilot import SEED

LABEL_PATH = Path(__file__).with_name("cluster_labels.json")
REVIEWED_COORDINATES_SHA256 = "a8e4bddbb7799d12aefb3dea6d491d14a476116b9a9beb64a8e44ca1351ab5e2"
PORTRAIT_FIRST_ORDER = (0, 4, 5, 15, 6, 1, 12, 14, 8, 9, 10, 11, 2, 13, 7, 3)


def display_clusters(points: pd.DataFrame, order: tuple[int, ...]) -> pd.DataFrame:
    if sorted(order) != list(range(16)):
        raise ValueError("Display order must contain all 16 original cluster IDs exactly once")
    result = points.copy()
    result["original_cluster"] = result["cluster"]
    result["cluster"] = result.original_cluster.map({old: new for new, old in enumerate(order)})
    if result.cluster.isna().any():
        raise ValueError("Unknown cluster ID in fitted coordinates")
    return result


def load_labels(count: int) -> dict[int, dict[str, str]]:
    data = json.loads(LABEL_PATH.read_text(encoding="utf-8"))
    if set(data) != {str(i) for i in range(count)}:
        raise ValueError("Cluster descriptions must cover every cluster exactly once")
    if any(not item.get("label") or not item.get("basis") for item in data.values()):
        raise ValueError("Every provisional label needs an evidence basis")
    return {int(k): value for k, value in data.items()}


def exact_centers(points: np.ndarray, bounds: tuple[float, float, float, float]) -> np.ndarray:
    """Uniform affine transform; preserve all t-SNE positions, with raster y reversed."""
    if points.ndim != 2 or points.shape[1] != 2 or not len(points) or not np.isfinite(points).all():
        raise ValueError("Expected nonempty finite 2D coordinates")
    x0, y0, x1, y1 = bounds
    if x1 <= x0 or y1 <= y0:
        raise ValueError("Invalid drawing bounds")
    low, high = points.min(axis=0), points.max(axis=0)
    span = high - low
    scale = min((x1 - x0) / max(span[0], 1e-12), (y1 - y0) / max(span[1], 1e-12))
    offsets = (points - (low + high) / 2) * scale
    return np.column_stack(((x0 + x1) / 2 + offsets[:, 0],
                            (y0 + y1) / 2 - offsets[:, 1]))


def render_exact_atlas(points: pd.DataFrame, output: Path, colors: list,
                       labels: dict[int, dict[str, str]]) -> dict:
    width, height = 2400, 1500
    bounds = (75.0, 115.0, 1840.0, 1370.0)
    centers = exact_centers(points[["tsne_x", "tsne_y"]].to_numpy(), bounds)
    placement = points[["record_id", "filename", "cluster", "tsne_x", "tsne_y"]].copy()
    placement["original_cluster"] = points.original_cluster
    placement["pdf_center_x"], placement["pdf_center_y"] = centers[:, 0], centers[:, 1]
    order = np.random.default_rng(SEED).permutation(len(points))
    draw_orders = np.empty(len(points), dtype=int)
    draw_orders[order] = np.arange(len(points))
    placement["draw_order"] = draw_orders
    placement["max_thumbnail_points"] = 15.0
    clean_width, clean_height = 2400, 1350
    clip = fitz.Rect(centers[:, 0].min() - 7.625, centers[:, 1].min() - 7.625,
                     centers[:, 0].max() + 7.625, centers[:, 1].max() + 7.625)
    clean_scale = min((clean_width - 24) / clip.width, (clean_height - 24) / clip.height)
    clean_rect = fitz.Rect(
        (clean_width - clip.width * clean_scale) / 2,
        (clean_height - clip.height * clean_scale) / 2,
        (clean_width + clip.width * clean_scale) / 2,
        (clean_height + clip.height * clean_scale) / 2,
    )
    clean_centers = (centers - [clip.x0, clip.y0]) * clean_scale + [clean_rect.x0, clean_rect.y0]
    placement["clean_pdf_center_x"], placement["clean_pdf_center_y"] = clean_centers.T
    placement["clean_max_thumbnail_points"] = 15 * clean_scale
    placement.to_csv(output / "tsne_atlas_placements.csv", index=False)
    bg = (38 / 255,) * 3
    white = (0.93,) * 3
    with fitz.open() as document:
        document.new_page(width=clean_width, height=clean_height)
        document.new_page(width=clean_width, height=clean_height)
        document.new_page(width=width, height=height)
        document.new_page(width=clean_width, height=clean_height)
        plain_page, portrait_page, page, clean_page = [document[i] for i in range(4)]
        for target in (plain_page, portrait_page, page, clean_page):
            target.draw_rect(target.rect, color=bg, fill=bg)
        page.insert_text((70, 58), "MAN RAY SPACE / actual t-SNE image positions", fontsize=31, color=white)
        page.insert_text((70, 88), f"{len(points):,} originals | No grid displacement | Thumbnails overlap in dense regions", fontsize=17, color=white)
        # Bounded transparent PDF batches avoid quadratic single-page resource growth.
        for start in range(0, len(order), 250):
            with fitz.open() as batch:
                for _ in range(3):
                    batch.new_page(width=width, height=height)
                layer, plain_layer, portrait_layer = [batch[i] for i in range(3)]
                for index in order[start:start + 250]:
                    row = points.iloc[index]
                    with Image.open(Path(row.image_path)) as source:
                        image = ImageOps.exif_transpose(source).convert("RGB")
                    image.thumbnail((90, 90), Image.Resampling.LANCZOS)
                    buffer = io.BytesIO()
                    image.save(buffer, format="JPEG", quality=85)
                    w, h = image.size
                    scale = 15 / max(w, h)
                    x, y = centers[index]
                    rect = fitz.Rect(x - w * scale / 2, y - h * scale / 2,
                                     x + w * scale / 2, y + h * scale / 2)
                    image_xref = layer.insert_image(rect, stream=buffer.getvalue())
                    plain_layer.insert_image(rect, xref=image_xref)
                    portrait_layer.insert_image(rect, xref=image_xref)
                    layer.draw_rect(rect, color=tuple(colors[int(row.cluster)][:3]), width=0.25)
                    if int(row.cluster) <= 9:
                        portrait_layer.draw_rect(rect, color=tuple(colors[int(row.cluster)][:3]), width=0.25)
                page.show_pdf_page(page.rect, batch, 0)
                clean_page.show_pdf_page(clean_rect, batch, 0, clip=clip)
                plain_page.show_pdf_page(clean_rect, batch, 1, clip=clip)
                portrait_page.show_pdf_page(clean_rect, batch, 2, clip=clip)
            if (start + 250) % 1000 == 0 or start + 250 >= len(order):
                print(f"Exact t-SNE atlas: {min(start + 250, len(order)):,}/{len(order):,} thumbnails embedded",
                      flush=True)
        page.insert_text((1900, 140), "PROVISIONAL DESCRIPTIONS", fontsize=18, color=white)
        page.insert_text((1900, 167), "16 clusters, IDs 0-15 / not a validated taxonomy", fontsize=13, color=white)
        for k, description in labels.items():
            y = 212 + k * 66
            page.draw_rect(fitz.Rect(1900, y - 13, 1918, y + 5), color=colors[k][:3], fill=colors[k][:3])
            page.insert_text((1930, y), f"{k}: {description['label']}", fontsize=15, color=white)
            count = int(points.cluster.eq(k).sum())
            page.insert_text((1930, y + 22),
                             f"n = {count:,} | {count / len(points):.1%} of all {len(points):,} images",
                             fontsize=12, color=white)
        page.insert_text((70, 1420), "Exact thumbnail centers match the fitted t-SNE coordinates under a uniform scale and y-axis reversal.", fontsize=15, color=white)
        page.insert_text((70, 1445), "All images are embedded; some are occluded. Use the grid atlas to see every tile. Labels describe tendencies, not every member.", fontsize=14, color=white)
        page.insert_text((70, 1470), "RGB (38,38,38) | Original polarity | Run-specific descriptions: see legend CSV for evidence and review status", fontsize=13, color=white)
        document.save(output / "space_tsne_image_atlas.pdf", deflate=True)
        page.get_pixmap(matrix=fitz.Matrix(4, 4), alpha=False).save(output / "space_tsne_image_atlas.png")
        page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False).save(output / "space_tsne_image_atlas_preview.png")
        clean_page.get_pixmap(matrix=fitz.Matrix(4, 4), alpha=False).save(output / "space_tsne_image_atlas_clean.png")
        clean_page.get_pixmap(alpha=False).save(output / "space_tsne_image_atlas_clean_preview.png")
        for target, suffix in ((plain_page, "no_outlines"), (portrait_page, "clusters_00_09")):
            target.get_pixmap(matrix=fitz.Matrix(4, 4), alpha=False).save(output / f"space_tsne_image_atlas_{suffix}.png")
            target.get_pixmap(alpha=False).save(output / f"space_tsne_image_atlas_{suffix}_preview.png")
    return {
        "images": len(points), "page_points": [width, height], "png_pixels": [9600, 6000],
        "bounds_points": list(bounds), "thumbnail_max_points": 15,
        "placement": "uniform affine mapping of original t-SNE centers; y reversed; no displacement",
        "draw_order": f"seeded permutation {SEED}; overlap and occlusion allowed",
        "label_sha256": hashlib.sha256(LABEL_PATH.read_bytes()).hexdigest(),
        "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "reviewed_coordinates_sha256": REVIEWED_COORDINATES_SHA256,
        "pages": 4, "page_order": ["no_outlines", "clusters_00_09", "labeled", "all_outlines"],
        "clean_page_points": [clean_width, clean_height],
        "clean_png_pixels": [9600, 5400], "clean_thumbnail_max_points": 15 * clean_scale,
        "clean_center_bounds": [float(clean_centers[:, 0].min()), float(clean_centers[:, 1].min()),
                                float(clean_centers[:, 0].max()), float(clean_centers[:, 1].max())],
        "clean_content_rect": list(clean_rect),
    }
