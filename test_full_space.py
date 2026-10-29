import unittest

import numpy as np
import pandas as pd

from full_space import spatial_cells
from tsne_atlas import PORTRAIT_FIRST_ORDER, display_clusters, exact_centers, load_labels


class SpatialGridTests(unittest.TestCase):
    def test_requested_cluster_order_preserves_membership(self):
        points = pd.DataFrame({"cluster": range(16), "tsne_x": np.arange(16) * 2})
        original = points.copy()
        displayed = display_clusters(points, PORTRAIT_FIRST_ORDER)
        labels = load_labels(16)
        expected = [
            "Seated portraits / marked prints", "Seated portraits / negatives",
            "Half-length portraits / prints", "Bust portraits / gestures / prints",
            "Front-facing portraits / negatives", "Dark-toned portrait prints",
            "Portraits / poses / negatives", "Full-length / fashion / costume",
            "Interiors / people in settings", "Groups / horizontal scenes",
            "Reproductions / framed forms", "Architecture / landscapes / travel",
            "Mounted images / graphic material", "Body studies / expressive poses",
            "Objects / masks / graphic forms", "Film edges / perforations",
        ]
        self.assertEqual([labels[old]["label"] for old in PORTRAIT_FIRST_ORDER], expected)
        self.assertEqual(displayed.sort_values("cluster").original_cluster.tolist(),
                         list(PORTRAIT_FIRST_ORDER))
        np.testing.assert_array_equal(displayed.tsne_x, original.tsne_x)
        pd.testing.assert_frame_equal(points, original)
        with self.assertRaises(ValueError):
            display_clusters(points, (0,) * 16)
        with self.assertRaises(ValueError):
            display_clusters(pd.DataFrame({"cluster": [16]}), PORTRAIT_FIRST_ORDER)

    def test_distinct_cells_for_uneven_and_identical_coordinates(self):
        for count, columns, rows in ((11965, 110, 109), (17, 5, 4), (1, 1, 1), (9, 1, 9), (9, 9, 1)):
            for points in (np.random.default_rng(17).normal(size=(count, 2)), np.zeros((count, 2))):
                cells = spatial_cells(points, columns, rows)
                self.assertEqual(len(np.unique(cells, axis=0)), count)
                self.assertTrue(((cells[:, 0] >= 0) & (cells[:, 0] < columns)).all())
                self.assertTrue(((cells[:, 1] >= 0) & (cells[:, 1] < rows)).all())
                np.testing.assert_array_equal(cells, spatial_cells(points, columns, rows))

    def test_invalid_grid_and_nonfinite_points(self):
        with self.assertRaises(ValueError):
            spatial_cells(np.zeros((5, 2)), 2, 2)
        with self.assertRaises(ValueError):
            spatial_cells(np.array([[float("nan"), 0]]), 1, 1)

    def test_exact_tsne_transform_preserves_shape_and_reverses_y(self):
        points = np.array([[0, 0], [10, 0], [0, 5], [4, 2]], dtype=float)
        centers = exact_centers(points, (20, 30, 220, 230))
        np.testing.assert_allclose(centers[1] - centers[0], [200, 0])
        np.testing.assert_allclose(centers[2] - centers[0], [0, -100])
        np.testing.assert_allclose(centers[3] - centers[0], [80, -40])
        self.assertTrue((centers[:, 0] >= 20).all())
        self.assertTrue((centers[:, 1] >= 30).all())
        self.assertEqual(len(load_labels(16)), 16)
        with self.assertRaises(ValueError):
            load_labels(15)
        with self.assertRaises(ValueError):
            exact_centers(np.array([[np.inf, 0]]), (0, 0, 1, 1))


if __name__ == "__main__":
    unittest.main()
