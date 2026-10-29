"""Full-collection exploratory PCA, neighborhood maps, and dark image atlases."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import textwrap
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageOps

from pilot import PROJECT, SEED, SOURCE, audit, embeddings
from tsne_atlas import (
    PORTRAIT_FIRST_ORDER, REVIEWED_COORDINATES_SHA256, display_clusters,
    load_labels, render_exact_atlas,
)

BACKGROUND = (38, 38, 38)
BG = "#262626"
FOREGROUND = "#eeeeee"
CLUSTERS = 16


def spatial_cells(points: np.ndarray, columns: int, rows: int) -> np.ndarray:
    """Assign every point a distinct grid cell by recursive balanced spatial cuts."""
    if len(points) > columns * rows or columns < 1 or rows < 1:
        raise ValueError("Grid has insufficient capacity")
    if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all():
        raise ValueError("Expected finite 2D coordinates")
    cells = np.empty((len(points), 2), dtype=int)

    def split(indices: np.ndarray, x: int, y: int, width: int, height: int) -> None:
        if not len(indices):
            return
        if width == height == 1:
            if len(indices) != 1:
                raise ValueError("Grid assignment collision")
            cells[indices[0]] = (x, y)
            return
        horizontal = width >= height and width > 1
        axis = 0 if horizontal else 1
        ordered = indices[np.argsort(points[indices, axis], kind="stable")]
        if horizontal:
            cut = width // 2
            left_capacity, right_capacity = cut * height, (width - cut) * height
        else:
            cut = height // 2
            left_capacity, right_capacity = cut * width, (height - cut) * width
        count = max(len(indices) - right_capacity,
                    min(left_capacity, round(len(indices) * left_capacity / (width * height))))
        if horizontal:
            split(ordered[:count], x, y, cut, height)
            split(ordered[count:], x + cut, y, width - cut, height)
        else:
            split(ordered[:count], x, y, width, cut)
            split(ordered[count:], x, y + cut, width, height - cut)

    split(np.arange(len(points)), 0, 0, columns, rows)
    return cells


def thumbnail(path: Path, size: int) -> Image.Image:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
    return ImageOps.pad(image, (size, size), color=BACKGROUND)


def fit_space(features: np.ndarray, records: pd.DataFrame) -> tuple[pd.DataFrame, dict, np.ndarray]:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    from sklearn.metrics import normalized_mutual_info_score, silhouette_score
    from threadpoolctl import threadpool_limits

    points = records.copy()
    print("Fitting PCA and high-dimensional clusters...", flush=True)
    with threadpool_limits(limits=4):
        pca = PCA(n_components=32, svd_solver="randomized", random_state=SEED)
        scores = pca.fit_transform(features)
        cluster_model = KMeans(n_clusters=CLUSTERS, n_init=20, random_state=SEED)
        labels = cluster_model.fit_predict(scores)
        silhouette = silhouette_score(scores, labels, sample_size=min(2000, len(scores)), random_state=SEED)
        print("Fitting all-image t-SNE neighborhood layout...", flush=True)
        xy = TSNE(
            n_components=2, perplexity=40, init="pca", learning_rate="auto",
            random_state=SEED, max_iter=1000, n_jobs=4,
        ).fit_transform(scores)
    points["pca_x"], points["pca_y"] = scores[:, 0], scores[:, 1]
    points["tsne_x"], points["tsne_y"] = xy[:, 0], xy[:, 1]
    points["cluster"] = labels
    points["distance_to_cluster_center"] = np.linalg.norm(scores - cluster_model.cluster_centers_[labels], axis=1)
    columns = int(np.ceil(np.sqrt(len(points))))
    rows = int(np.ceil(len(points) / columns))
    # Reverse y for raster coordinates so the atlas matches the scatter's orientation.
    grid = spatial_cells(xy * [1, -1], columns, rows)
    points["atlas_column"], points["atlas_row"] = grid[:, 0], grid[:, 1]
    points["embedding_row"] = np.arange(len(points))
    summary = {
        "pca_explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
        "pca_first_two_variance": float(pca.explained_variance_ratio_[:2].sum()),
        "pca_first_32_variance": float(pca.explained_variance_ratio_.sum()),
        "kmeans_clusters": CLUSTERS,
        "clustering_space": "32 PCA components of original-image L2-normalized 512D ResNet18 features",
        "silhouette_sample_2000": float(silhouette),
        "cluster_medium_nmi": float(normalized_mutual_info_score(records.medium_group, labels)),
        "cluster_counts": {str(k): int((labels == k).sum()) for k in range(CLUSTERS)},
        "tsne": {"perplexity": 40, "max_iter": 1000, "seed": SEED},
        "atlas": {"columns": columns, "rows": rows, "tile_pixels": 120,
                  "assignment": "recursive spatial cuts; displaces coordinates; not a distance-preserving map"},
    }
    return points, summary, scores


def render(points: pd.DataFrame, summary: dict, output: Path) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
        "text.color": FOREGROUND, "axes.labelcolor": FOREGROUND,
        "xtick.color": FOREGROUND, "ytick.color": FOREGROUND,
        "axes.edgecolor": "#888888", "pdf.fonttype": 42, "font.size": 11,
        "legend.facecolor": BG, "legend.edgecolor": "#777777",
    })
    palette = plt.get_cmap("tab20")
    colors = [palette(i) for i in range(CLUSTERS)]
    descriptions = load_labels(CLUSTERS)
    coordinate_hash = hashlib.sha256((output / "coordinates.csv").read_bytes()).hexdigest()
    reviewed = coordinate_hash == REVIEWED_COORDINATES_SHA256
    if not reviewed:
        warnings.warn("Coordinates differ from the reviewed run. Semantic descriptions are withheld; "
                      "review the new detail sheets before assigning labels.", stacklevel=2)
        descriptions = {
            k: {"label": f"Cluster {k} / not reviewed", "basis": "New fitted run; no semantic review"}
            for k in range(CLUSTERS)
        }
    order = tuple(summary.get("presentation_cluster_order", range(CLUSTERS)))
    points = display_clusters(points, order)
    colors = [colors[old] for old in order]
    descriptions = {new: descriptions[old] for new, old in enumerate(order)}
    points.to_csv(output / "display_coordinates.csv", index=False)
    n = len(points)
    pages = 0
    plotted = {}
    selections = []
    with PdfPages(output / "man_ray_space.pdf") as pdf:
        def save(fig, filename=None):
            nonlocal pages
            fig.text(0.025, 0.018,
                     f"EXPLORATORY | {n:,} linked images; {int(points.man_ray_exact.sum()):,} attributed exactly to Man Ray | Original images | Seed {SEED}",
                     fontsize=9)
            pdf.savefig(fig, facecolor=BG)
            if filename:
                fig.savefig(output / filename, dpi=240, facecolor=BG)
            plt.close(fig)
            pages += 1

        fig = plt.figure(figsize=(16, 9))
        fig.text(0.07, 0.83, "MAN RAY SPACE", fontsize=38, weight="bold")
        lines = [
            f"{n:,} catalog-linked images / no sampling",
            "A visual exploration of the Pompidou catalog scrape",
            "PCA: broad variation  |  t-SNE: local neighborhoods  |  k-means: exploratory groupings",
            "Sixteen groups chosen for inspection, not sixteen discovered historical categories",
            "Negatives retained as photographed; no sitter identity or gender inferred",
            f"{summary['status_counts'].get('missing_image', 0)} missing downloads; "
            f"{summary['status_counts'].get('missing_url', 0)} blank catalog URLs; gray placeholder excluded",
            "44 records have other/shared artist fields; attribution overlay and CSV retain them",
            "Source thumbnails are ~500 pixels; map geometry does not establish artistic intention",
        ]
        for i, line in enumerate(lines):
            fig.text(0.07, 0.69 - 0.065 * i, line, fontsize=16)
        save(fig)

        def map_page(kind: str, column: str, title: str, filename: str,
                     only_man_ray: bool = False) -> None:
            frame = points[points.man_ray_exact] if only_man_ray else points
            fig, ax = plt.subplots(figsize=(16, 9))
            if column == "cluster":
                for k in range(CLUSTERS):
                    subset = frame[frame.cluster.eq(k)]
                    ax.scatter(subset[f"{kind}_x"], subset[f"{kind}_y"], color=colors[k],
                               s=5, alpha=0.8, linewidths=0,
                               label=f"{k}: {textwrap.fill(descriptions[k]['label'], 28)}\n"
                                     f"n = {len(subset):,} ({len(subset) / len(frame):.1%})")
                for k in range(CLUSTERS):
                    subset = frame[frame.cluster.eq(k)]
                    if len(subset):
                        center = subset[[f"{kind}_x", f"{kind}_y"]].median().to_numpy()
                        ax.text(*center, str(k), color="white", fontsize=12, weight="bold",
                                bbox={"facecolor": BG, "alpha": 0.75, "edgecolor": "none", "pad": 2})
            else:
                for i, group in enumerate(sorted(frame[column].unique(), key=str)):
                    subset = frame[frame[column].eq(group)]
                    label = str(group)
                    if column == "man_ray_exact":
                        label = "Man Ray (exact artist field)" if group else "Other/shared artist field"
                    ax.scatter(subset[f"{kind}_x"], subset[f"{kind}_y"], color=palette(i * 2),
                               s=5 if column != "man_ray_exact" or group else 35, alpha=0.8,
                               linewidths=0,
                               label=f"{label}: {len(subset):,} ({len(subset) / len(frame):.1%})")
            ax.set_title(title, fontsize=22, pad=20)
            ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1),
                      fontsize=7 if column == "cluster" else 9, markerscale=3,
                      title="Provisional descriptions" if column == "cluster" else None)
            if kind == "pca":
                variance = summary["space"]["pca_explained_variance_ratio"]
                ax.set_xlabel(f"PC1: {variance[0]:.1%} of feature variance")
                ax.set_ylabel(f"PC2: {variance[1]:.1%} of feature variance")
            else:
                ax.set_aspect("equal", adjustable="box")
                ax.set_xlim(points.tsne_x.min() - 5, points.tsne_x.max() + 5)
                ax.set_ylim(points.tsne_y.min() - 5, points.tsne_y.max() + 5)
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_xlabel("t-SNE: neighborhoods for exploration; global distances and island sizes are not evidence")
            fig.tight_layout(rect=(0.02, 0.055, 0.98, 0.98))
            plotted[filename] = len(frame)
            save(fig, filename)

        map_page("pca", "cluster", "Man Ray space / PCA / all linked images", "space_pca.png")
        map_page("tsne", "cluster", "Man Ray space / visual neighborhoods / all linked images", "space_tsne.png")
        map_page("tsne", "cluster", "Man Ray attribution subset / same fitted coordinates", "space_man_ray_only.png", True)
        map_page("tsne", "medium_group", "Same visual space / catalog medium", "space_medium.png")
        map_page("tsne", "date_band", "Same visual space / catalog date bands (uncertainty retained in CSV)", "space_dates.png")
        map_page("tsne", "subject_group", "Same visual space / title-derived categories, not complete subject labels", "space_titles.png")
        map_page("tsne", "man_ray_exact", "Same visual space / attribution audit", "space_attribution.png")

        fig = plt.figure(figsize=(16, 9))
        fig.text(0.05, 0.94, "A provisional semantic key / 16 clusters, IDs 0-15", fontsize=25)
        fig.text(0.05, 0.89,
                 "Reviewed examples + catalog evidence; overlapping tendencies, not validated labels for every image"
                 if reviewed else "New fitted run: semantic descriptions withheld until the detail sheets are reviewed",
                 fontsize=13)
        for k in range(CLUSTERS):
            x, y = 0.05 + (k // 8) * 0.49, 0.81 - (k % 8) * 0.089
            fig.text(x, y, f"{k}  {descriptions[k]['label']}", color=colors[k], fontsize=14, weight="bold")
            group = points[points.cluster.eq(k)]
            counts = group.medium_group.value_counts()
            dominant = str(counts.index[0])
            fig.text(x + 0.015, y - 0.028,
                     f"n = {len(group):,} ({len(group) / n:.1%} of all images); "
                     f"{int(counts.iloc[0]) / len(group):.0%} medium: {dominant}",
                     fontsize=11)
        fig.savefig(output / "cluster_semantic_legend.pdf", facecolor=BG)
        save(fig, "cluster_semantic_legend.png")

        for k in range(CLUSTERS):
            group = points[points.cluster.eq(k)].sort_values("distance_to_cluster_center")
            center = group.head(6)
            rest = group.loc[~group.record_id.isin(center.record_id)]
            random = rest.sample(min(3, len(rest)), random_state=SEED + order[k])
            edge = rest.loc[~rest.record_id.isin(random.record_id)].tail(3).iloc[::-1]
            chosen = pd.concat([center.assign(role="center"), random.assign(role="random"),
                                edge.assign(role="edge")])
            fig, axes = plt.subplots(3, 4, figsize=(16, 9))
            for ax in axes.flat:
                ax.axis("off")
            for ax, row in zip(axes.flat, chosen.itertuples()):
                ax.imshow(thumbnail(Path(row.image_path), 320))
                ax.set_title(f"{row.role} | #{row.record_id} | {row.medium_group}\n{str(row.title)[:52]}",
                             fontsize=8, color=FOREGROUND)
                selections.append({"cluster": k, "original_cluster": order[k],
                                   "record_id": row.record_id, "role": row.role})
            fig.suptitle(f"{k}: {descriptions[k]['label']} / n = {len(group):,} ({len(group) / n:.1%})\nProvisional description; originals shown", fontsize=20)
            fig.tight_layout(rect=(0.01, 0.055, 0.99, 0.94))
            save(fig, f"neighborhood_{k:02d}.png")

        fig = plt.figure(figsize=(16, 9))
        fig.text(0.07, 0.86, "Reading the space", fontsize=28)
        text = [
            f"PC1 + PC2 explain {summary['space']['pca_first_two_variance']:.1%} of embedding variance.",
            f"The 32-component clustering space explains {summary['space']['pca_first_32_variance']:.1%}.",
            f"Sampled silhouette: {summary['space']['silhouette_sample_2000']:.3f}; groups are not sharply isolated.",
            "Cluster numbers are arbitrary identifiers, not ranked categories or a validated taxonomy.",
            "All original frames retained: polarity, film edges, support color and subject can all affect grouping.",
            "PCA and t-SNE share the same features, but show different aspects of their structure.",
            "The grid atlas removes overlap; the exact t-SNE atlas retains positions but permits occlusion.",
            "Three byte-duplicate pairs remain: catalog records and collection objects are not automatically merged.",
            "Next: inspect neighborhoods; test border handling and stronger embeddings; validate with human review.",
        ]
        for i, line in enumerate(text):
            fig.text(0.07, 0.74 - i * 0.065, line, fontsize=15)
        save(fig)

    pd.DataFrame(selections).to_csv(output / "detail_selections.csv", index=False)
    atlas_spec = summary["space"]["atlas"]
    tile = atlas_spec["tile_pixels"]
    width, height = atlas_spec["columns"] * tile, atlas_spec["rows"] * tile
    canvas = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    for row in points.itertuples():
        x, y = row.atlas_column * tile, row.atlas_row * tile
        canvas.paste(thumbnail(Path(row.image_path), tile - 6), (x + 3, y + 3))
        color = tuple(round(c * 255) for c in colors[row.cluster][:3])
        draw.rectangle((x, y, x + tile - 1, y + tile - 1), outline=color, width=2)
        draw.rectangle((x + 3, y + tile - 15, x + tile - 3, y + tile - 3), fill=BACKGROUND)
        draw.text((x + 4, y + tile - 15), f"{row.record_id} / {row.cluster}", fill=FOREGROUND)
    canvas.save(output / "space_image_atlas.png")
    canvas.save(output / "space_image_atlas.pdf", resolution=240)
    canvas.thumbnail((2200, 2200))
    canvas.save(output / "space_image_atlas_preview.png")
    label_rows = [
        {"cluster": k, "original_cluster": order[k], "label": value["label"], "basis": value["basis"],
         "color_hex": "#" + "".join(f"{round(c * 255):02x}" for c in colors[k][:3]),
         "count": int(points.cluster.eq(k).sum()), "status": "provisional" if reviewed else "not reviewed",
         "percentage": 100 * int(points.cluster.eq(k).sum()) / n,
         "percentage_denominator": n,
         "coordinates_sha256": coordinate_hash}
        for k, value in descriptions.items()
    ]
    pd.DataFrame(label_rows).to_csv(output / "cluster_semantic_legend.csv", index=False)
    exact_atlas = render_exact_atlas(points, output, colors, descriptions)
    exact_atlas["semantic_review_matches_coordinates"] = reviewed
    return {"presentation_pages": pages, "plotted_counts": plotted,
            "atlas_tiles": len(points), "atlas_pixels": [width, height],
            "background_rgb": list(BACKGROUND), "detail_images": len(selections),
            "display_to_original_cluster": list(order),
            "exact_tsne_atlas": exact_atlas}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=PROJECT / "outputs" / "full_space")
    parser.add_argument("--batch-size", type=int, default=48)
    parser.add_argument("--render-only", action="store_true",
                        help="Re-export figures from this run's existing coordinates and summary")
    parser.add_argument("--portrait-first", action="store_true",
                        help="Renumber presentation groups in the requested portrait-first order; preserve fit IDs")
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if output == source or source in output.parents or output in source.parents:
        parser.error("Output must be separate from source")
    if args.batch_size < 1:
        parser.error("Batch size must be positive")
    if args.render_only:
        summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        points = pd.read_csv(output / "coordinates.csv", keep_default_na=False)
    else:
        if output.exists() and any(output.iterdir()):
            parser.error("Nonempty output; choose a new --output or --render-only")
        output.mkdir(parents=True, exist_ok=True)
        records, summary = audit(source, output)
        records = records[records.status.eq("linked")].sort_values("record_id").reset_index(drop=True)
        if records.filename.duplicated().any():
            raise ValueError("Multiple catalog records per local filename; resolve before fitting")
        summary.update(
            source=str(source), seed=SEED, images=len(records), python=platform.python_version(),
            packages={name: importlib.metadata.version(name) for name in
                      ("numpy", "pandas", "Pillow", "scikit-learn", "matplotlib", "PyMuPDF")},
        )
        original, _, summary["model"] = embeddings(records, output, args.batch_size, positive_views=False)
        print("All image embeddings saved.", flush=True)
        points, summary["space"], scores = fit_space(original, records)
        np.save(output / "pca_scores.npy", scores)
        points.to_csv(output / "coordinates.csv", index=False)
        (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("Rendering dark presentation, detail sheets and full spatial atlas...", flush=True)
    if args.portrait_first:
        summary["presentation_cluster_order"] = list(PORTRAIT_FIRST_ORDER)
    summary["exports"] = render(points, summary, output)
    summary["render_code_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Completed full collection space: {output}", flush=True)


if __name__ == "__main__":
    main()
