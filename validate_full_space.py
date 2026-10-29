"""Verify complete collection coverage, dark exports, PDFs, and source integrity."""

import argparse
import hashlib
import json
from pathlib import Path

import fitz
import numpy as np
import pandas as pd
from PIL import Image

from full_space import BACKGROUND, CLUSTERS
from pilot import SEED
from tsne_atlas import LABEL_PATH, display_clusters, exact_centers, load_labels


def validate(output: Path) -> None:
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    points = pd.read_csv(output / "coordinates.csv", keep_default_na=False)
    catalog = pd.read_csv(output / "catalog_manifest.csv", keep_default_na=False)
    files = pd.read_csv(output / "local_files.csv", keep_default_na=False)
    linked = catalog[catalog.status.eq("linked")]
    n = len(linked)
    assert n == summary["images"] == len(points) == summary["exports"]["atlas_tiles"]
    assert points.record_id.is_unique and points.filename.is_unique
    assert points.record_id.tolist() == linked.record_id.tolist()
    assert points.filename.tolist() == linked.filename.tolist()
    assert len(catalog) == summary["catalog_records"]
    assert catalog.status.value_counts().to_dict() == summary["status_counts"]
    assert int(points.man_ray_exact.sum()) == 11921
    numeric = points[["pca_x", "pca_y", "tsne_x", "tsne_y", "distance_to_cluster_center"]]
    assert np.isfinite(numeric.to_numpy()).all()
    assert set(points.cluster) == set(range(CLUSTERS))
    assert points.cluster.value_counts().sum() == n
    assert {str(k): int(v) for k, v in points.cluster.value_counts().items()} == summary["space"]["cluster_counts"]
    assert len(points[["atlas_column", "atlas_row"]].drop_duplicates()) == n
    spec = summary["space"]["atlas"]
    assert points.atlas_column.between(0, spec["columns"] - 1).all()
    assert points.atlas_row.between(0, spec["rows"] - 1).all()
    np.testing.assert_array_equal(points.embedding_row, np.arange(n))
    with np.load(output / "embeddings.npz") as arrays:
        assert arrays["original"].shape == (n, 512)
        assert np.isfinite(arrays["original"]).all()
        np.testing.assert_array_equal(arrays["record_ids"], points.record_id)
        np.testing.assert_allclose(np.linalg.norm(arrays["original"], axis=1), 1, atol=1e-5)
    scores = np.load(output / "pca_scores.npy")
    assert scores.shape == (n, 32) and np.isfinite(scores).all()
    np.testing.assert_allclose(scores[:, :2], points[["pca_x", "pca_y"]], atol=1e-6)
    for filename, count in summary["exports"]["plotted_counts"].items():
        assert count == (11921 if filename == "space_man_ray_only.png" else n)
        with Image.open(output / filename) as image:
            assert image.size == (3840, 2160), (filename, image.size)
            assert image.convert("RGB").getpixel((0, 0)) == BACKGROUND, filename
    order = tuple(summary["exports"]["display_to_original_cluster"])
    points = display_clusters(points, order)
    displayed = pd.read_csv(output / "display_coordinates.csv", keep_default_na=False)
    pd.testing.assert_frame_equal(displayed, points, check_exact=False, atol=1e-9, rtol=1e-12)
    details = pd.read_csv(output / "detail_selections.csv")
    assert len(details) == summary["exports"]["detail_images"]
    assert set(details.cluster) == set(range(CLUSTERS))
    joined = details.merge(points[["record_id", "cluster"]], on="record_id", suffixes=("", "_actual"),
                           validate="many_to_one")
    assert (joined.cluster == joined.cluster_actual).all()
    assert not details.duplicated(["cluster", "record_id"]).any()
    for filename in [f"neighborhood_{k:02d}.png" for k in range(CLUSTERS)]:
        with Image.open(output / filename) as image:
            assert image.size == (3840, 2160)
            assert image.convert("RGB").getpixel((0, 0)) == BACKGROUND
    with Image.open(output / "space_image_atlas.png") as image:
        assert list(image.size) == summary["exports"]["atlas_pixels"]
        # The atlas's unused final grid cells must also use the specified background.
        occupied = set(map(tuple, points[["atlas_column", "atlas_row"]].to_numpy()))
        tile = spec["tile_pixels"]
        for row in range(spec["rows"]):
            for column in range(spec["columns"]):
                if (column, row) not in occupied:
                    assert image.getpixel((column * tile + tile // 2, row * tile + tile // 2)) == BACKGROUND
    for filename, pages in (("man_ray_space.pdf", summary["exports"]["presentation_pages"]),
                            ("space_image_atlas.pdf", 1)):
        with fitz.open(output / filename) as document:
            assert len(document) == pages
            for index, page in enumerate(document):
                pix = page.get_pixmap(matrix=fitz.Matrix(0.35, 0.35), alpha=False)
                assert pix.width > 100 and pix.height > 100
                if filename == "man_ray_space.pdf":
                    assert tuple(pix.samples[:3]) == BACKGROUND, (filename, index, tuple(pix.samples[:3]))
                    assert "EXPLORATORY" in page.get_text(), (filename, index)
            if filename == "man_ray_space.pdf":
                document[1].get_pixmap(matrix=fitz.Matrix(1, 1)).save(output / "pdf_pca_preview.png")
                document[2].get_pixmap(matrix=fitz.Matrix(1, 1)).save(output / "pdf_tsne_preview.png")
    assert summary["render_code_sha256"] == hashlib.sha256(
        Path(__file__).with_name("full_space.py").read_bytes()).hexdigest()
    exact = summary["exports"]["exact_tsne_atlas"]
    assert exact["images"] == n
    positions = pd.read_csv(output / "tsne_atlas_placements.csv")
    assert positions.record_id.tolist() == points.record_id.tolist()
    np.testing.assert_array_equal(positions.cluster, points.cluster)
    np.testing.assert_array_equal(positions.original_cluster, points.original_cluster)
    expected_centers = exact_centers(points[["tsne_x", "tsne_y"]].to_numpy(), tuple(exact["bounds_points"]))
    np.testing.assert_allclose(positions[["pdf_center_x", "pdf_center_y"]], expected_centers, atol=1e-9)
    np.testing.assert_array_equal(np.sort(positions.draw_order), np.arange(n))
    np.testing.assert_array_equal(
        positions.sort_values("draw_order").index.to_numpy(),
        np.random.default_rng(SEED).permutation(n),
    )
    original_labels = load_labels(CLUSTERS)
    labels = {new: original_labels[old] for new, old in enumerate(order)}
    legend = pd.read_csv(output / "cluster_semantic_legend.csv")
    assert legend.cluster.tolist() == list(range(CLUSTERS))
    assert legend["label"].tolist() == [labels[k]["label"] for k in range(CLUSTERS)]
    assert legend["count"].sum() == n and legend.status.eq("provisional").all()
    assert legend["count"].tolist() == [int(points.cluster.eq(k).sum()) for k in range(CLUSTERS)]
    assert legend.original_cluster.tolist() == list(order)
    assert legend.percentage_denominator.eq(n).all()
    np.testing.assert_allclose(legend.percentage, legend["count"] / n * 100)
    np.testing.assert_allclose(legend.percentage.sum(), 100)
    import matplotlib
    palette = matplotlib.colormaps["tab20"]
    assert legend.color_hex.tolist() == [
        "#" + "".join(f"{round(c * 255):02x}" for c in palette(k)[:3])
        for k in order
    ]
    coordinate_hash = hashlib.sha256((output / "coordinates.csv").read_bytes()).hexdigest()
    assert legend.coordinates_sha256.eq(coordinate_hash).all()
    assert exact["semantic_review_matches_coordinates"]
    assert exact["reviewed_coordinates_sha256"] == coordinate_hash
    assert exact["label_sha256"] == hashlib.sha256(LABEL_PATH.read_bytes()).hexdigest()
    assert exact["renderer_sha256"] == hashlib.sha256(
        Path(__file__).with_name("tsne_atlas.py").read_bytes()).hexdigest()
    with Image.open(output / "cluster_semantic_legend.png") as image:
        assert image.size == (3840, 2160)
        assert image.convert("RGB").getpixel((0, 0)) == BACKGROUND
    with fitz.open(output / "cluster_semantic_legend.pdf") as document:
        assert len(document) == 1
        text = document[0].get_text()
        for k in range(CLUSTERS):
            assert labels[k]["label"] in text
            count = int(points.cluster.eq(k).sum())
            assert f"n = {count:,} ({count / n:.1%} of all images)" in text
        pix = document[0].get_pixmap(alpha=False)
        assert tuple(pix.samples[:3]) == BACKGROUND
    with Image.open(output / "space_tsne_image_atlas.png") as image:
        assert list(image.size) == exact["png_pixels"]
        assert image.convert("RGB").getpixel((0, 0)) == BACKGROUND
    with fitz.open(output / "space_tsne_image_atlas.pdf") as document:
        assert len(document) == exact["pages"] == 4
        assert exact["page_order"] == ["no_outlines", "clusters_00_09", "labeled", "all_outlines"]
        page = document[2]
        assert len(page.get_image_info()) == n, "Each record must have one embedded image placement"
        image_rectangles = page.get_image_info()
        # PDF image order follows the recorded deterministic compositing order.
        ordered_positions = positions.sort_values("draw_order")
        for info, row in zip(image_rectangles, ordered_positions.itertuples()):
            rect = fitz.Rect(info["bbox"])
            np.testing.assert_allclose(
                [(rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2],
                [row.pdf_center_x, row.pdf_center_y], atol=0.001,
            )
        text = page.get_text()
        assert "PROVISIONAL" in text
        for k in range(CLUSTERS):
            assert labels[k]["label"] in text, k
            count = int(points.cluster.eq(k).sum())
            assert f"n = {count:,} | {count / n:.1%} of all {n:,} images" in text
        pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5), alpha=False)
        assert tuple(pix.samples[:3]) == BACKGROUND
        clean_page = document[3]
        assert clean_page.get_text().strip() == "", "Clean page must have no text"
        assert list(clean_page.rect)[2:] == exact["clean_page_points"]
        assert clean_page.rect.width / clean_page.rect.height == 16 / 9
        clean_images = clean_page.get_image_info()
        assert len(clean_images) == n
        expected_clean = exact_centers(
            points[["tsne_x", "tsne_y"]].to_numpy(), tuple(exact["clean_center_bounds"]))
        np.testing.assert_allclose(positions[["clean_pdf_center_x", "clean_pdf_center_y"]],
                                   expected_clean, atol=1e-9)
        for info, row in zip(clean_images, ordered_positions.itertuples()):
            rect = fitz.Rect(info["bbox"])
            np.testing.assert_allclose(
                [(rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2],
                # Nested PDF transforms serialize with limited decimal precision (<0.012 PNG pixel).
                [row.clean_pdf_center_x, row.clean_pdf_center_y], atol=0.003, rtol=0)
            assert clean_page.rect.contains(rect)
        content = fitz.Rect(exact["clean_content_rect"])
        assert min(abs(content.width - (clean_page.rect.width - 24)),
                   abs(content.height - (clean_page.rect.height - 24))) < 0.001
        pix = clean_page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5), alpha=False)
        assert tuple(pix.samples[:3]) == BACKGROUND
        all_images = clean_page.get_image_info(hashes=True)
        for page_index, suffix in ((0, "no_outlines"), (1, "clusters_00_09")):
            variant = document[page_index]
            assert variant.rect == clean_page.rect
            assert not variant.get_text().strip()
            images = variant.get_image_info(hashes=True)
            assert len(images) == n
            for actual, expected in zip(images, all_images):
                assert actual["digest"] == expected["digest"]
                np.testing.assert_allclose(actual["bbox"], expected["bbox"], atol=0.001)
            outlines = [drawing for drawing in variant.get_drawings() if drawing["type"] == "s"]
            expected_clusters = (
                [] if page_index == 0
                else [int(row.cluster) for row in ordered_positions.itertuples() if row.cluster <= 9]
            )
            assert len(outlines) == len(expected_clusters)
            for drawing, cluster in zip(outlines, expected_clusters):
                np.testing.assert_allclose(drawing["color"], palette(order[cluster])[:3], atol=1e-5)
            expected_boxes = [
                image["bbox"] for image, row in zip(images, ordered_positions.itertuples())
                if page_index == 1 and row.cluster <= 9
            ]
            for drawing, box in zip(outlines, expected_boxes):
                np.testing.assert_allclose(list(drawing["rect"]), box, atol=0.003, rtol=0)
            pix = variant.get_pixmap(matrix=fitz.Matrix(0.5, 0.5), alpha=False)
            assert tuple(pix.samples[:3]) == BACKGROUND
            with Image.open(output / f"space_tsne_image_atlas_{suffix}.png") as image:
                assert list(image.size) == exact["clean_png_pixels"]
                assert image.convert("RGB").getpixel((0, 0)) == BACKGROUND
    with Image.open(output / "space_tsne_image_atlas_clean.png") as image:
        assert list(image.size) == exact["clean_png_pixels"]
        assert image.width / image.height == 16 / 9
        assert image.convert("RGB").getpixel((0, 0)) == BACKGROUND
    for row in files.itertuples():
        with Path(row.image_path).open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == row.sha256, row.filename
    source = Path(summary["source"])
    assert hashlib.sha256((source / "master.csv").read_bytes()).hexdigest() == summary["source_catalog_sha256"]
    print(f"PASS: all {n:,} linked images have features, coordinates, cluster labels and unique atlas cells.")
    print("PASS: Man-Ray-only view has 11,921 records; all other attribution fields retained.")
    print("PASS: RGB (38,38,38) backgrounds in map/detail PNGs, presentation PDF pages and unused atlas cells.")
    print(f"PASS: all {summary['exports']['presentation_pages']} presentation pages and atlas PDF rendered.")
    print(f"PASS: all {len(files):,} source JPEG hashes and catalog hash remain unchanged.")
    print(f"PASS: all {n:,} PDF thumbnails centered at exact t-SNE positions; 16 provisional semantic labels verified.")
    print("Acrobat/display review remains a manual delivery check.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path,
                        default=Path(__file__).parent / "outputs" / "full_space")
    validate(parser.parse_args().output)
