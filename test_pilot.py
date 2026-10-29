import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from pilot import audit, date_band, local_filename, medium_group, prepare_image, stratified_sample, subject_group


class PilotTests(unittest.TestCase):
    def test_url_linkage(self):
        self.assertEqual(local_filename("https://example.org/media/picture/18/a9/abcdef/thumb_medium.jpg"),
                         "18_a9_abcdef.jpg")
        self.assertEqual(local_filename(""), "")
        self.assertEqual(local_filename("https://example.org/not-an-image"), "")

    def test_catalog_labels_and_uncertain_dates(self):
        self.assertEqual(medium_group("Négatif sur verre"), "negative")
        self.assertEqual(medium_group("Epreuve gélatino-argentique"), "print")
        self.assertEqual(medium_group(""), "other_unknown")
        self.assertEqual(date_band("vers 1930"), "1930s")
        self.assertEqual(date_band("1929 - 1931"), "range")
        self.assertEqual(date_band("sans date"), "unknown")
        self.assertEqual(subject_group("Portrait de femme non identifiée"), "portrait")

    def test_sampling_is_deterministic_unique_and_covers_strata(self):
        records = pd.DataFrame({
            "record_id": range(60),
            "medium_group": ["negative"] * 30 + ["print"] * 30,
            "date_band": ["1930s"] * 60,
            "subject_group": ["portrait"] * 60,
        })
        a = stratified_sample(records, 24, 17)
        b = stratified_sample(records, 24, 17)
        pd.testing.assert_frame_equal(a, b)
        self.assertEqual(a.record_id.nunique(), 24)
        self.assertEqual(set(a.medium_group), {"negative", "print"})
        self.assertEqual(len(stratified_sample(records, 60, 17)), 60)
        with self.assertRaises(ValueError):
            stratified_sample(records, 61, 17)

    def test_inversion_preserves_source_and_full_frame(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "image.png"
            Image.new("RGB", (100, 50), (10, 20, 30)).save(path)
            original = path.read_bytes()
            normal = np.array(prepare_image(path, False))
            inverse = np.array(prepare_image(path, True))
            self.assertEqual(normal.shape, (224, 224, 3))
            np.testing.assert_array_equal(normal[112, 112], [10, 20, 30])
            np.testing.assert_array_equal(inverse[112, 112], [245, 235, 225])
            np.testing.assert_array_equal(normal[0, 0], [128, 128, 128])
            self.assertEqual(path.read_bytes(), original)

    def test_audit_accounts_for_missing_unmatched_and_duplicate_files(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            images = source / "images"
            images.mkdir(parents=True)
            output = Path(directory) / "output"
            output.mkdir()
            Image.new("RGB", (20, 30), (10, 20, 30)).save(images / "aa_bb_hash.jpg")
            (images / "other.jpg").write_bytes((images / "aa_bb_hash.jpg").read_bytes())
            rows = [
                {"img": "https://example.org/picture/aa/bb/hash/thumb.jpg", "title": "Portrait",
                 "artist": "Man Ray", "date": "vers 1930", "medium": "Négatif", "inv": "A"},
                {"img": "", "title": "Unknown", "artist": "Man Ray", "date": "1931",
                 "medium": "", "inv": "B"},
                {"img": "https://example.org/picture/xx/yy/missing/thumb.jpg", "title": "Unknown",
                 "artist": "Man Ray", "date": "1932", "medium": "", "inv": "C"},
            ]
            pd.DataFrame(rows).to_csv(source / "master.csv", index=False)
            manifest, summary = audit(source, output)
            self.assertEqual(summary["linked_unique_files"], 1)
            self.assertEqual(summary["duplicate_groups"], 1)
            self.assertEqual(summary["extra_byte_copies"], 1)
            self.assertEqual(summary["unmatched_local_files"], ["other.jpg"])
            self.assertEqual(manifest.status.tolist(), ["linked", "missing_url", "missing_image"])
            self.assertEqual(len(list(images.iterdir())), 2)


if __name__ == "__main__":
    unittest.main()
