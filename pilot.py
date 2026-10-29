"""Local, reproducible collection audit and exploratory image-embedding pilot."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageOps

SEED = 20261017
PROJECT = Path(__file__).resolve().parent
SOURCE = Path(r"E:\PM_laptop_backup\mydocs\MR_scrape")
SUBJECT_PATTERNS = {
    "portrait": r"portrait|autoportrait",
    "unidentified_person": r"personne.*non identifi",
    "fashion": r"\bmode\b",
    "rayograph": r"rayograph",
    "landscape": r"paysage",
    "reproduction": r"reproduction",
    "body_study": r"\bnu(?:e|s|es)?\b",
}


def local_filename(url: str) -> str:
    """Translate the museum image URL to the existing scrape's naming scheme."""
    match = re.search(r"/picture/([^/]+)/([^/]+)/([^/]+)/", urlparse(url).path)
    return "_".join(match.groups()) + ".jpg" if match else ""


def medium_group(medium: str) -> str:
    text = medium.casefold()
    if "négatif" in text or "negatif" in text:
        return "negative"
    if text.startswith(("epreuve", "épreuve")):
        return "print"
    return "other_unknown"


def date_band(value: str) -> str:
    years = re.findall(r"\b(?:18|19|20)\d{2}\b", value)
    if not years:
        return "unknown"
    if len(set(years)) > 1:
        return "range"
    year = int(years[0])
    return f"{year // 10 * 10}s"


def subject_group(title: str) -> str:
    for name, pattern in SUBJECT_PATTERNS.items():
        if re.search(pattern, title, flags=re.IGNORECASE):
            return name
    return "other_title"


def inspect_file(path: Path) -> dict[str, object]:
    with path.open("rb") as stream:
        sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
    result: dict[str, object] = {
        "filename": path.name,
        "image_path": str(path.resolve()),
        "sha256": sha256,
        "bytes": path.stat().st_size,
        "width": 0,
        "height": 0,
        "read_error": "",
    }
    try:
        with Image.open(path) as image:
            image.load()
            result.update(width=image.width, height=image.height)
    except (OSError, ValueError) as error:
        result["read_error"] = f"{type(error).__name__}: {error}"
    return result


def audit(source: Path, output: Path) -> tuple[pd.DataFrame, dict]:
    images = source / "images"
    catalog_path = source / "master.csv"
    if not images.is_dir() or not catalog_path.is_file():
        raise FileNotFoundError(f"Expected images folder and master.csv under {source}")
    catalog = pd.read_csv(catalog_path, dtype=str, keep_default_na=False)
    required = {"img", "title", "artist", "date", "medium", "inv"}
    if not required.issubset(catalog.columns):
        raise ValueError(f"Missing catalog columns: {sorted(required - set(catalog.columns))}")
    catalog.insert(0, "record_id", np.arange(1, len(catalog) + 1))
    catalog["filename"] = catalog["img"].map(local_filename)
    paths = sorted(images.glob("*.jpg"))
    if not paths:
        raise ValueError(f"No JPEG files under {images}")
    with ThreadPoolExecutor(max_workers=8) as pool:
        files = pd.DataFrame(pool.map(inspect_file, paths))
    if files.filename.duplicated().any():
        raise ValueError("Ambiguous local filenames")
    manifest = catalog.merge(files, on="filename", how="left", validate="many_to_one")
    manifest["status"] = np.where(manifest.image_path.notna(), "linked", "missing_image")
    manifest.loc[manifest.img.eq(""), "status"] = "missing_url"
    manifest.loc[manifest.read_error.fillna("").ne(""), "status"] = "unreadable"
    manifest["medium_group"] = manifest.medium.map(medium_group)
    manifest["date_band"] = manifest.date.map(date_band)
    manifest["subject_group"] = manifest.title.map(subject_group)
    manifest["man_ray_exact"] = manifest.artist.eq("Man Ray")
    manifest["date_uncertain"] = manifest.date.str.contains(
        r"vers|avant|après|entre|\?|ca\.|circa", case=False, regex=True
    )
    for label, pattern in SUBJECT_PATTERNS.items():
        manifest[f"title_flag_{label}"] = manifest.title.str.contains(pattern, case=False, regex=True)
    duplicate_files = files[files.sha256.duplicated(keep=False)].sort_values(["sha256", "filename"])
    duplicates = duplicate_files.merge(
        catalog[["filename", "record_id", "inv", "title", "artist"]],
        on="filename", how="left", validate="one_to_many",
    )
    unmatched = files[~files.filename.isin(catalog.filename)]
    manifest.to_csv(output / "catalog_manifest.csv", index=False)
    files.to_csv(output / "local_files.csv", index=False)
    manifest[manifest.status.ne("linked")].to_csv(output / "missing_or_unreadable.csv", index=False)
    unmatched.to_csv(output / "unmatched_local_files.csv", index=False)
    duplicates.to_csv(output / "duplicate_review.csv", index=False)
    summary = {
        "catalog_records": len(catalog),
        "local_files": len(files),
        "status_counts": manifest.status.value_counts().to_dict(),
        "linked_unique_files": int(manifest.loc[manifest.status.eq("linked"), "filename"].nunique()),
        "unmatched_local_files": unmatched.filename.tolist(),
        "duplicate_groups": int(duplicate_files.sha256.nunique()),
        "extra_byte_copies": int(duplicate_files.sha256.duplicated().sum()),
        "unreadable_local_files": int(files.read_error.ne("").sum()),
        "linked_artist_counts": manifest.loc[manifest.status.eq("linked"), "artist"].value_counts().to_dict(),
        "linked_medium_counts": manifest.loc[manifest.status.eq("linked"), "medium_group"].value_counts().to_dict(),
        "source_catalog_sha256": hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
    }
    if summary["unreadable_local_files"]:
        raise ValueError("Unreadable image files found; inspect local_files.csv before continuing")
    return manifest, summary


def stratified_sample(records: pd.DataFrame, count: int, seed: int) -> pd.DataFrame:
    """Round-robin joint strata; intentionally favors coverage, not prevalence."""
    if count < 24 or count > len(records):
        raise ValueError(f"Sample size must be between 24 and {len(records)}")
    rng = np.random.default_rng(seed)
    groups = [
        rng.permutation(group.index.to_numpy()).tolist()
        for _, group in records.groupby(["medium_group", "date_band", "subject_group"], sort=True)
    ]
    selected = []
    while len(selected) < count:
        for position in rng.permutation(len(groups)):
            if groups[position]:
                selected.append(groups[position].pop())
                if len(selected) == count:
                    break
    return records.loc[selected].sort_values("record_id").reset_index(drop=True)


def prepare_image(path: Path, invert: bool, size: int = 224) -> Image.Image:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
    if invert:
        image = ImageOps.invert(image)
    # Preserve the full frame; borders are a documented sensitivity concern.
    return ImageOps.pad(image, (size, size), color=(128, 128, 128))


def embeddings(sample: pd.DataFrame, output: Path, batch_size: int,
               positive_views: bool = True) -> tuple[np.ndarray, np.ndarray, dict]:
    import torch
    import torchvision
    from torchvision.models import ResNet18_Weights, resnet18
    from torchvision.transforms import Normalize, ToTensor

    torch.manual_seed(SEED)
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    torch.hub.set_dir(str(output.parent / ".model-cache"))
    weights = ResNet18_Weights.IMAGENET1K_V1
    model = resnet18(weights=weights)
    model.fc = torch.nn.Identity()
    model.eval()
    tensorize = ToTensor()
    normalize = Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

    def encode(rows: pd.DataFrame, positive_view: bool) -> np.ndarray:
        result = []
        for start in range(0, len(rows), batch_size):
            batch = rows.iloc[start:start + batch_size]
            tensors = [
                normalize(tensorize(prepare_image(
                    Path(row.image_path), positive_view and row.medium_group == "negative"
                )))
                for row in batch.itertuples()
            ]
            with torch.inference_mode():
                result.append(model(torch.stack(tensors)).numpy())
            print(f"Encoded {'positive-view' if positive_view else 'original'} {min(start + batch_size, len(rows))}/{len(rows)}", flush=True)
        matrix = np.concatenate(result)
        return matrix / np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12)

    original = encode(sample, False)
    positive = original.copy()
    negatives = sample.medium_group.eq("negative").to_numpy()
    if positive_views and negatives.any():
        positive[negatives] = encode(sample[negatives], True)
    metadata = {
        "model": "torchvision ResNet18 IMAGENET1K_V1, pooled layer before classifier",
        "torch": torch.__version__,
        "torchvision": torchvision.__version__,
        "embedding_dimensions": original.shape[1],
        "preprocessing": "EXIF orientation; RGB; full-frame 224-square gray letterbox; ImageNet normalization",
        "inversion": ("RGB 255-x only for catalog-medium negatives; exploratory, not print reconstruction"
                      if positive_views else "Disabled; all embeddings use originals"),
        "device": "cpu",
        "torch_threads": 4,
        "weights_sha256": hashlib.sha256(
            (output.parent / ".model-cache" / "checkpoints" / "resnet18-f37072fd.pth").read_bytes()
        ).hexdigest(),
    }
    arrays = {"original": original, "record_ids": sample.record_id.to_numpy()}
    if positive_views:
        arrays["positive_view"] = positive
    np.savez_compressed(output / "embeddings.npz", **arrays)
    return original, positive, metadata


def analyze(matrix: np.ndarray, medium: pd.Series, seed: int) -> tuple[np.ndarray, np.ndarray, dict, np.ndarray]:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    from sklearn.metrics import normalized_mutual_info_score, silhouette_score
    from sklearn.neighbors import NearestNeighbors

    high = PCA(n_components=min(32, len(matrix) - 1), random_state=seed).fit_transform(matrix)
    labels = KMeans(n_clusters=8, n_init=20, random_state=seed).fit_predict(high)
    coordinates = TSNE(
        n_components=2, perplexity=min(30, (len(matrix) - 1) / 3),
        init="pca", learning_rate="auto", random_state=seed,
    ).fit_transform(high)
    neighbors = NearestNeighbors(n_neighbors=11, metric="cosine").fit(matrix).kneighbors(
        matrix, return_distance=False
    )
    # Explicitly remove self even when identical vectors produce tied neighbors.
    neighbors = np.array([[j for j in row if j != i][:10] for i, row in enumerate(neighbors)])
    groups = medium.to_numpy()
    same = np.mean(groups[neighbors] == groups[:, None])
    n = len(groups)
    random_same = sum(int((groups == group).sum()) * (int((groups == group).sum()) - 1)
                      for group in np.unique(groups)) / (n * (n - 1))
    metrics = {
        "kmeans_clusters": 8,
        "silhouette_pca_euclidean": float(silhouette_score(high, labels)),
        "cluster_medium_normalized_mutual_information": float(normalized_mutual_info_score(groups, labels)),
        "same_medium_fraction_in_10_neighbors": float(same),
        "random_neighbor_same_medium_expectation": float(random_same),
        "cluster_counts": {str(k): int((labels == k).sum()) for k in sorted(set(labels))},
        "pca_dimensions": high.shape[1],
        "layout": "t-SNE, PCA initialization, perplexity up to 30",
        "clustering_space": "32-component PCA of L2-normalized 512-dimensional embeddings; NOT the 2D layout",
    }
    return coordinates, labels, metrics, neighbors


def render(sample: pd.DataFrame, positive: np.ndarray,
           layouts: dict, labels: dict, summary: dict, output: Path) -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    plt.rcParams.update({"pdf.fonttype": 42, "font.size": 11})
    palette = plt.get_cmap("tab10")
    n = len(sample)
    columns, tile = 24, 160
    rows = (n + columns - 1) // columns
    atlas = Image.new("RGB", (columns * tile, rows * tile + 100), "white")
    draw = ImageDraw.Draw(atlas)
    order = np.argsort(labels["positive_view"], kind="stable")
    assert len(set(order.tolist())) == n
    for position, index in enumerate(order):
        row = sample.iloc[index]
        x, y = (position % columns) * tile, (position // columns) * tile
        image = prepare_image(Path(row.image_path), False, tile - 8)
        atlas.paste(image, (x + 4, y + 4))
        color = tuple(int(channel * 255) for channel in palette(int(labels["positive_view"][index]))[:3])
        draw.rectangle((x, y, x + tile - 1, y + tile - 1), outline=color, width=4)
        draw.rectangle((x + 4, y + tile - 20, x + tile - 4, y + tile - 4), fill="white")
        draw.text((x + 6, y + tile - 20), f"#{row.record_id} / C{labels['positive_view'][index]}", fill="black")
    draw.text((20, rows * tile + 20), f"PILOT ONLY: all {n} selected images, sorted by positive-view cluster; originals shown.", fill="black")
    draw.text((20, rows * tile + 50), "Colored borders indicate exploratory cluster. IDs link to pilot_coordinates.csv; this is not a spatial embedding.", fill="black")
    atlas.save(output / "pilot_atlas.png")
    atlas.save(output / "pilot_atlas.pdf", resolution=240)
    page_count = 0
    with PdfPages(output / "pilot_presentation.pdf") as pdf:
        def save(fig, name=None):
            nonlocal page_count
            fig.text(0.02, 0.015, f"PILOT: {n:,} selected images, not the full collection | Seed {SEED} | Exploratory, unvalidated groups", fontsize=9)
            pdf.savefig(fig)
            if name:
                fig.savefig(output / name, dpi=200)
            plt.close(fig)
            page_count += 1

        fig = plt.figure(figsize=(16, 9))
        fig.text(0.07, 0.86, "Man Ray / Pompidou: a collection-scale pilot", fontsize=28)
        lines = [
            f"{summary['catalog_records']:,} catalog records; {summary['linked_unique_files']:,} linked local images.",
            f"{n:,} sampled records; all artists retained and explicitly recorded.",
            "Joint-stratified selection: medium x date band x title-derived subject.",
            "Coverage sample, not a representative estimate of collection proportions.",
            "ResNet-18 embeddings; 8 k-means groups in PCA space; t-SNE for display only.",
            "Compare originals with provisional positive views of catalog-labeled negatives.",
            "Full frames retained; borders and digitization effects may influence similarity.",
            "No sitter gender or identity inferred from appearance.",
            "500-pixel sources limit detail; independent layouts cannot be compared by position.",
        ]
        for index, line in enumerate(lines):
            fig.text(0.07, 0.73 - index * 0.065, line, fontsize=15)
        save(fig)

        fig, axes = plt.subplots(1, 2, figsize=(16, 9))
        for ax, frame, title in (
            (axes[0], pd.read_csv(output / "catalog_manifest.csv").query("status == 'linked'"), "All linked catalog records"),
            (axes[1], sample, f"Pilot: {n} images (oversamples rare strata)"),
        ):
            counts = frame.medium_group.value_counts().reindex(["negative", "print", "other_unknown"], fill_value=0)
            ax.bar(counts.index, counts.values, color=["#456990", "#e9a23b", "#888888"])
            ax.set_title(title)
            ax.set_ylabel("Catalog records")
            for i, value in enumerate(counts):
                ax.text(i, value, f"{value:,}", ha="center", va="bottom")
        fig.suptitle("Coverage before interpretation", fontsize=23)
        fig.tight_layout(rect=(0.03, 0.06, 0.98, 0.92))
        save(fig)

        for variant in ("original", "positive_view"):
            xy = layouts[variant]
            fig, axes = plt.subplots(1, 2, figsize=(16, 9))
            axes[0].scatter(
                xy[:, 0], xy[:, 1], c=[palette(int(label)) for label in labels[variant]],
                s=24, alpha=0.85,
            )
            axes[0].set_title("Eight exploratory visual groups")
            for label in range(8):
                center = np.median(xy[labels[variant] == label], axis=0)
                axes[0].text(*center, str(label), fontsize=15, weight="bold")
            for group, color in (("negative", "#456990"), ("print", "#e9a23b"), ("other_unknown", "#888888")):
                mask = sample.medium_group.eq(group).to_numpy()
                axes[1].scatter(xy[mask, 0], xy[mask, 1], color=color, label=group, s=24, alpha=0.85)
            axes[1].legend()
            axes[1].set_title("Same positions, catalog medium overlay")
            for ax in axes:
                ax.set_xticks([])
                ax.set_yticks([])
            fig.suptitle(f"Pilot visual map: {variant.replace('_', ' ')}", fontsize=23)
            fig.tight_layout(rect=(0.02, 0.05, 0.98, 0.92))
            save(fig, f"map_{variant}.png")

        xy = layouts["positive_view"]
        fig, axes = plt.subplots(1, 2, figsize=(16, 9))
        for ax, column, title in (
            (axes[0], "date_band", "Catalog date bands (not exact capture dates)"),
            (axes[1], "subject_group", "Title-derived flags (not complete subject labels)"),
        ):
            for index, group in enumerate(sorted(sample[column].unique())):
                mask = sample[column].eq(group).to_numpy()
                ax.scatter(xy[mask, 0], xy[mask, 1], color=palette(index), label=group, s=22, alpha=0.8)
            ax.set_title(title)
            ax.legend(fontsize=9, loc="best")
            ax.set_xticks([])
            ax.set_yticks([])
        fig.suptitle("Same positive-view map, different catalog overlays", fontsize=23)
        fig.tight_layout(rect=(0.02, 0.05, 0.98, 0.92))
        save(fig, "map_catalog_overlays.png")

        fig, axes = plt.subplots(3, 4, figsize=(16, 9))
        negatives = np.flatnonzero(sample.medium_group.eq("negative").to_numpy())[:6]
        for ax in axes.flat:
            ax.axis("off")
        for pair, index in enumerate(negatives):
            row = sample.iloc[index]
            for side in range(2):
                ax = axes.flat[pair * 2 + side]
                ax.imshow(prepare_image(Path(row.image_path), bool(side), 280))
                ax.set_title(f"Record {row.record_id}: {'inverted preview' if side else 'original'}", fontsize=9)
        fig.suptitle("Polarity review: digital inversion is not a reconstructed print", fontsize=22)
        fig.tight_layout(rect=(0.01, 0.05, 0.99, 0.93))
        save(fig, "polarity_review.png")

        # Original thumbnails stay visible even when selection uses transformed embeddings.
        matrix = positive
        for label in range(8):
            members = np.flatnonzero(labels["positive_view"] == label)
            center = matrix[members].mean(axis=0)
            distances = np.linalg.norm(matrix[members] - center, axis=1)
            ranked = members[np.argsort(distances)]
            representative = ranked[:min(6, len(ranked))]
            remainder = np.array([i for i in members if i not in representative], dtype=int)
            rng = np.random.default_rng(SEED + label)
            random_rows = rng.choice(remainder, size=min(3, len(remainder)), replace=False)
            used = set(representative) | set(random_rows)
            boundary = np.array([i for i in ranked[::-1] if i not in used][:3], dtype=int)
            chosen = list(representative) + list(random_rows) + list(boundary)
            roles = ["center"] * len(representative) + ["random"] * len(random_rows) + ["edge"] * len(boundary)
            fig, axes = plt.subplots(3, 4, figsize=(16, 9))
            for ax in axes.flat:
                ax.axis("off")
            for ax, index, role in zip(axes.flat, chosen, roles):
                row = sample.iloc[index]
                ax.imshow(prepare_image(Path(row.image_path), False, 280))
                title = str(row.title)
                ax.set_title(f"{role} | #{row.record_id} | {row.medium_group}\n{title[:44]}", fontsize=8)
            fig.suptitle(f"Positive-view cluster {label}: {len(members)} pilot images; originals shown", fontsize=21)
            fig.tight_layout(rect=(0.01, 0.05, 0.99, 0.93))
            save(fig, f"cluster_{label}.png")

        fig = plt.figure(figsize=(16, 9))
        fig.text(0.07, 0.88, "Pilot evidence and limitations", fontsize=26)
        metrics = summary["analysis"]
        text = [
            f"Mean overlap of ten nearest neighbors between variants: {metrics['mean_neighbor_overlap']:.1%}",
            f"Original cluster / medium NMI: {metrics['original']['cluster_medium_normalized_mutual_information']:.3f}",
            f"Positive-view cluster / medium NMI: {metrics['positive_view']['cluster_medium_normalized_mutual_information']:.3f}",
            "Lower medium association is a diagnostic, not proof of better subject recognition.",
            "K-means forces every sample into a group; eight is a pilot setting, not a discovered truth.",
            "t-SNE islands and distances do not establish historical categories or artistic intention.",
            "Polarity views and borders need manual review; attribution is retained, not assumed.",
            "Dates and title terms are catalog evidence, not exact dates or complete subject labels.",
            "Next: human review, a stronger embedding comparison, then a full collection atlas.",
        ]
        for i, line in enumerate(text):
            fig.text(0.07, 0.75 - i * 0.065, line, fontsize=15)
        save(fig)
    return page_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=PROJECT / "outputs" / "pilot")
    parser.add_argument("--sample-size", type=int, default=384)
    parser.add_argument("--batch-size", type=int, default=24)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    output = args.output.resolve()
    source = args.source.resolve()
    if output == source or source in output.parents or output in source.parents:
        parser.error("Output must be separate from the source tree")
    if output.exists() and any(output.iterdir()):
        parser.error("Output folder is not empty; choose a new --output to preserve previous runs")
    output.mkdir(parents=True, exist_ok=True)
    print("Auditing source files and catalog...", flush=True)
    manifest, summary = audit(source, output)
    eligible = manifest[manifest.status.eq("linked")]
    if eligible.filename.duplicated().any():
        raise ValueError("Multiple catalog records link to one file; resolve before sampling")
    sample = stratified_sample(eligible, args.sample_size, SEED)
    sample.to_csv(output / "pilot_sample.csv", index=False)
    summary.update({
        "seed": SEED, "sample_size": len(sample), "source": str(source),
        "sampling": "Seeded round-robin joint strata: medium_group x date_band x subject_group; not population representative",
        "sample_medium_counts": sample.medium_group.value_counts().to_dict(),
        "sample_date_counts": sample.date_band.value_counts().to_dict(),
        "sample_subject_counts": sample.subject_group.value_counts().to_dict(),
        "python": platform.python_version(),
        "packages": {name: importlib.metadata.version(name) for name in
                     ("numpy", "pandas", "Pillow", "scikit-learn", "matplotlib")},
    })
    (output / "audit_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    original, positive, model_metadata = embeddings(sample, output, args.batch_size)
    layouts, labels, analysis, neighbors = {}, {}, {}, {}
    for name, matrix in (("original", original), ("positive_view", positive)):
        layouts[name], labels[name], analysis[name], neighbors[name] = analyze(matrix, sample.medium_group, SEED)
        sample[f"{name}_x"] = layouts[name][:, 0]
        sample[f"{name}_y"] = layouts[name][:, 1]
        sample[f"{name}_cluster"] = labels[name]
    overlap = [
        len(set(a) & set(b)) / 10
        for a, b in zip(neighbors["original"], neighbors["positive_view"])
    ]
    analysis["mean_neighbor_overlap"] = float(np.mean(overlap))
    sample["neighbor_overlap_fraction"] = overlap
    sample.to_csv(output / "pilot_coordinates.csv", index=False)
    summary.update(model=model_metadata, analysis=analysis)
    summary["atlas_tiles"] = len(sample)
    summary["pdf_pages"] = render(sample, positive, layouts, labels, summary, output)
    summary["code_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (output / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Completed {len(sample)}-image pilot: {output}", flush=True)


if __name__ == "__main__":
    main()
