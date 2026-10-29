"""Append a text-free atlas page highlighting one catalog-linked thumbnail."""

import argparse
import hashlib
import json
from pathlib import Path

import fitz
import numpy as np
import pandas as pd


def append_highlight(source: Path, output: Path, image_url: str) -> None:
    records = pd.read_csv(source / "display_coordinates.csv", keep_default_na=False)
    matches = records[records.img.eq(image_url)]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one catalog image URL match, found {len(matches)}")
    record = matches.iloc[0]
    placements = pd.read_csv(source / "tsne_atlas_placements.csv")
    placement = placements[placements.record_id.eq(record.record_id)]
    if len(placement) != 1:
        raise ValueError("Expected one recorded thumbnail placement")
    selected = placement.iloc[0]
    legend = pd.read_csv(source / "cluster_semantic_legend.csv")
    cluster = legend[legend.cluster.eq(record.cluster)]
    if len(cluster) != 1:
        raise ValueError("Expected one matching cluster color")
    color_hex = cluster.iloc[0].color_hex
    color = tuple(int(color_hex[i:i + 2], 16) / 255 for i in (1, 3, 5))
    source_pdf = source / "space_tsne_image_atlas.pdf"
    source_hash = hashlib.sha256(source_pdf.read_bytes()).hexdigest()
    if output.exists():
        raise FileExistsError(f"Choose a new output folder: {output}")
    output.mkdir(parents=True)
    with fitz.open(source_pdf) as original, fitz.open() as result:
        if len(original) != 4 or original[0].get_text().strip():
            raise ValueError("Expected the four-page atlas with a text-free first page")
        if any(item["type"] == "s" for item in original[0].get_drawings()):
            raise ValueError("Source first page must have no thumbnail outlines")
        original_images = original[0].get_image_info(hashes=True)
        if len(original_images) != len(records):
            raise ValueError("Source image placements do not cover the catalog records")
        target = fitz.Rect(original_images[int(selected.draw_order)]["bbox"])
        np.testing.assert_allclose(
            [(target.x0 + target.x1) / 2, (target.y0 + target.y1) / 2],
            [selected.clean_pdf_center_x, selected.clean_pdf_center_y], atol=0.003, rtol=0,
        )
        result.insert_pdf(original)
        result.insert_pdf(original, from_page=0, to_page=0)
        page = result[4]
        # Draw last so the locator remains visible even when the thumbnail is overlapped.
        page.draw_rect(target, color=color, width=1.5, overlay=True)
        pdf = output / "space_tsne_image_atlas.pdf"
        result.save(pdf, deflate=True)
    with fitz.open(source_pdf) as original, fitz.open(pdf) as result:
        assert len(result) == 5
        for i in range(4):
            assert original[i].get_pixmap(alpha=False).samples == result[i].get_pixmap(alpha=False).samples
        page = result[4]
        assert not page.get_text().strip()
        assert page.rect.width / page.rect.height == 16 / 9
        images = page.get_image_info(hashes=True)
        assert len(images) == len(original_images)
        for actual, expected in zip(images, original_images):
            assert actual["digest"] == expected["digest"]
            np.testing.assert_allclose(actual["bbox"], expected["bbox"], atol=1e-5)
        outlines = [item for item in page.get_drawings() if item["type"] == "s"]
        assert len(outlines) == 1
        np.testing.assert_allclose(list(outlines[0]["rect"]), list(target), atol=0.001)
        np.testing.assert_allclose(outlines[0]["color"], color, atol=1e-5)
        preview = page.get_pixmap(alpha=False)
        assert tuple(preview.samples[:3]) == (38, 38, 38)
        preview.save(output / "space_tsne_image_atlas_highlight_preview.png")
        page.get_pixmap(matrix=fitz.Matrix(4, 4), alpha=False).save(
            output / "space_tsne_image_atlas_highlight.png")
    assert hashlib.sha256(source_pdf.read_bytes()).hexdigest() == source_hash
    metadata = {
        "source_pdf": str(source_pdf.resolve()), "source_pdf_sha256": source_hash,
        "pages": 5, "highlight_page": 5, "image_url": image_url,
        "record_id": int(record.record_id), "filename": record.filename,
        "title": record.title, "inventory": record.inv,
        "display_cluster": int(record.cluster), "original_cluster": int(record.original_cluster),
        "color_hex": color_hex, "border_width_points": 1.5,
        "highlight_bbox_points": list(target), "png_pixels": [9600, 5400],
        "border_compositing": "above all thumbnails; no image displaced or redrawn",
        "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "validation": "first four pages pixel-identical; fifth page has identical images/positions and exactly one matching outline",
    }
    (output / "highlight_summary.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"PASS: five-page atlas; {len(images):,} images unchanged; one outline around "
          f"#{record.record_id} {record.title} ({record.inv}), cluster {record.cluster}.")
    print(f"Saved: {pdf}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-url", required=True)
    args = parser.parse_args()
    append_highlight(args.source, args.output, args.image_url)
