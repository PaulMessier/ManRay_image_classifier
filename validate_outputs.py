"""Check pilot coverage, source preservation, coordinates, atlas, and PDF rendering."""

import argparse
import hashlib
import json
from pathlib import Path

import fitz
import numpy as np
import pandas as pd
from PIL import Image


def validate(output: Path) -> None:
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    files = pd.read_csv(output / "local_files.csv", keep_default_na=False)
    manifest = pd.read_csv(output / "catalog_manifest.csv", keep_default_na=False)
    sample = pd.read_csv(output / "pilot_sample.csv", keep_default_na=False)
    points = pd.read_csv(output / "pilot_coordinates.csv", keep_default_na=False)
    missing = pd.read_csv(output / "missing_or_unreadable.csv", keep_default_na=False)
    unmatched = pd.read_csv(output / "unmatched_local_files.csv", keep_default_na=False)
    duplicates = pd.read_csv(output / "duplicate_review.csv", keep_default_na=False)
    count = summary["sample_size"]
    assert len(manifest) == summary["catalog_records"]
    assert len(files) == summary["local_files"]
    assert manifest.status.value_counts().to_dict() == summary["status_counts"]
    assert len(missing) + int(manifest.status.eq("linked").sum()) == len(manifest)
    assert len(unmatched) == len(summary["unmatched_local_files"])
    assert duplicates.sha256.nunique() == summary["duplicate_groups"]
    assert len(sample) == len(points) == count == summary["atlas_tiles"]
    assert sample.record_id.is_unique and sample.filename.is_unique
    assert points.record_id.tolist() == sample.record_id.tolist()
    assert set(sample.record_id).issubset(set(manifest.loc[manifest.status.eq("linked"), "record_id"]))
    current_code_hash = hashlib.sha256(Path(__file__).with_name("pilot.py").read_bytes()).hexdigest()
    if summary["code_sha256"] != current_code_hash:
        print("NOTE: pilot.py has changed since this historical pilot run; its recorded code hash "
              "describes the earlier version. Artifact and source integrity checks still follow.")
    source = Path(summary["source"])
    assert hashlib.sha256((source / "master.csv").read_bytes()).hexdigest() == summary["source_catalog_sha256"]
    for row in files.itertuples():
        with Path(row.image_path).open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == row.sha256, row.filename
    print(f"PASS: all {len(files):,} original JPEG hashes and the original catalog are unchanged.")

    with np.load(output / "embeddings.npz") as archive:
        for name in ("original", "positive_view"):
            features = archive[name]
            assert features.shape == (count, 512)
            assert np.isfinite(features).all()
            np.testing.assert_allclose(np.linalg.norm(features, axis=1), 1, atol=1e-5)
        np.testing.assert_array_equal(archive["record_ids"], sample.record_id.to_numpy())
        unchanged = sample.medium_group.ne("negative").to_numpy()
        np.testing.assert_array_equal(archive["original"][unchanged], archive["positive_view"][unchanged])
    for name in ("original", "positive_view"):
        coordinates = points[[f"{name}_x", f"{name}_y"]].to_numpy()
        assert coordinates.shape == (count, 2) and np.isfinite(coordinates).all()
        cluster_counts = points[f"{name}_cluster"].value_counts().to_dict()
        assert {str(k): int(v) for k, v in cluster_counts.items()} == summary["analysis"][name]["cluster_counts"]
        assert sum(cluster_counts.values()) == count
    with Image.open(output / "pilot_atlas.png") as atlas:
        assert atlas.size == (3840, ((count + 23) // 24) * 160 + 100)
        atlas.verify()
    print(f"PASS: all {count} selected records have valid embeddings, coordinates, cluster labels, and atlas allocation.")

    for filename, pages in (("pilot_presentation.pdf", summary["pdf_pages"]), ("pilot_atlas.pdf", 1)):
        with fitz.open(output / filename) as document:
            assert len(document) == pages, filename
            assert not document.is_encrypted
            for index, page in enumerate(document):
                pixmap = page.get_pixmap(matrix=fitz.Matrix(0.6, 0.6), alpha=False)
                assert pixmap.width > 100 and pixmap.height > 100
                if filename == "pilot_presentation.pdf":
                    text = page.get_text()
                    assert "PILOT:" in text, (filename, index)
                    assert f"{count:,}" in text, (filename, index)
            if filename == "pilot_presentation.pdf":
                document[0].get_pixmap(matrix=fitz.Matrix(1, 1)).save(output / "pdf_title_preview.png")
                document[-1].get_pixmap(matrix=fitz.Matrix(1, 1)).save(output / "pdf_findings_preview.png")
    print(f"PASS: rendered all {summary['pdf_pages']} presentation pages and the one-page atlas PDF.")
    print("Note: programmatic PDF rendering is not a substitute for review in Acrobat on the presentation display.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=Path(__file__).parent / "outputs" / "pilot")
    validate(parser.parse_args().output)
