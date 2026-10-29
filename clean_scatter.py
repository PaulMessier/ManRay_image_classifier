"""Render the t-SNE cluster scatter without any text, legend or frame, filling a 16:9 page."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

from full_space import BG, CLUSTERS
from tsne_atlas import PORTRAIT_FIRST_ORDER

WIDTH_IN, HEIGHT_IN = 16.0, 9.0
MARGIN_IN = 0.2
PNG_DPI = 600


def fitted_axes_rect(points: pd.DataFrame) -> tuple[float, float, float, float]:
    """Largest equal-aspect axes rectangle (figure fractions) for the data inside the margins."""
    pad = 5.0
    span_x = points.tsne_x.max() - points.tsne_x.min() + 2 * pad
    span_y = points.tsne_y.max() - points.tsne_y.min() + 2 * pad
    avail_w, avail_h = WIDTH_IN - 2 * MARGIN_IN, HEIGHT_IN - 2 * MARGIN_IN
    scale = min(avail_w / span_x, avail_h / span_y)
    w, h = span_x * scale, span_y * scale
    return ((WIDTH_IN - w) / 2 / WIDTH_IN, (HEIGHT_IN - h) / 2 / HEIGHT_IN, w / WIDTH_IN, h / HEIGHT_IN)


def render(points: pd.DataFrame, output: Path) -> dict:
    palette = plt.get_cmap("tab20")
    colors = [palette(old) for old in PORTRAIT_FIRST_ORDER]
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), facecolor=BG)
    ax = fig.add_axes(fitted_axes_rect(points), facecolor=BG)
    pad = 5.0
    for k in range(CLUSTERS):
        subset = points[points.cluster.eq(k)]
        ax.scatter(subset.tsne_x, subset.tsne_y, color=colors[k], s=5, alpha=0.8, linewidths=0)
    ax.set_xlim(points.tsne_x.min() - pad, points.tsne_x.max() + pad)
    ax.set_ylim(points.tsne_y.min() - pad, points.tsne_y.max() + pad)
    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()
    fig.savefig(output / "space_tsne_clean.pdf", facecolor=BG)
    fig.savefig(output / "space_tsne_clean.png", dpi=PNG_DPI, facecolor=BG)
    fig.savefig(output / "space_tsne_clean_preview.png", dpi=120, facecolor=BG)
    plt.close(fig)
    return {"text_artists": len(fig.texts) + len(ax.texts), "legend": ax.get_legend() is not None,
            "plotted": int(sum(len(c.get_offsets()) for c in ax.collections))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("outputs/full_space_four_page"))
    parser.add_argument("--output", type=Path, default=Path("outputs/full_space_clean_scatter"))
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit(f"Refusing to overwrite nonempty folder: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)

    source_csv = args.source / "display_coordinates.csv"
    points = pd.read_csv(source_csv, usecols=["record_id", "tsne_x", "tsne_y", "cluster", "original_cluster"])
    expected = {new: old for new, old in enumerate(PORTRAIT_FIRST_ORDER)}
    if not (points.original_cluster.map(lambda old: PORTRAIT_FIRST_ORDER.index(old)) == points.cluster).all():
        raise SystemExit("Display cluster IDs do not match PORTRAIT_FIRST_ORDER")

    result = render(points, args.output)
    with Image.open(args.output / "space_tsne_clean.png") as png:
        size = png.size
        background = png.convert("RGB").getpixel((2, 2))
    checks = {
        "points": len(points), "plotted": result["plotted"],
        "text_artists": result["text_artists"], "legend": result["legend"],
        "png_size": list(size), "png_corner_rgb": list(background),
    }
    if (result["plotted"] != len(points) or result["text_artists"] or result["legend"]
            or size != (int(WIDTH_IN * PNG_DPI), int(HEIGHT_IN * PNG_DPI)) or background != (38, 38, 38)):
        raise SystemExit(f"Validation failed: {checks}")
    summary = {
        "source": str(source_csv),
        "source_sha256": hashlib.sha256(source_csv.read_bytes()).hexdigest(),
        "display_order_original_ids": list(PORTRAIT_FIRST_ORDER),
        "colors": "matplotlib tab20 indexed by original cluster ID (same as space_tsne.png)",
        "marker": "s=5 pt^2, alpha 0.8, no edge; clusters drawn in display order 0-15 as in space_tsne.png",
        "page_inches": [WIDTH_IN, HEIGHT_IN], "margin_inches": MARGIN_IN,
        "cluster_map": expected, "validation": checks,
    }
    (args.output / "clean_scatter_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
