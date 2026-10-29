# Man Ray image classifier (Centre Pompidou catalogue)

An exploratory, collection-scale map of 11,965 Man Ray images scraped from the
Centre Pompidou online catalogue. Every image is embedded with an
ImageNet-trained ResNet18, reduced with PCA (32 components), grouped with
k-means (k = 16) and laid out with t-SNE. The results are presentation
graphics: an image atlas in which every thumbnail sits at its t-SNE position,
cluster detail sheets and a provisional semantic legend.

Main finding: the strongest organizing factor is **material state** (negative
versus print). Within that split, images group by portrait framing, by genre
and by physical artifacts of the archive (film edges, mounts). Clusters overlap
(silhouette 0.059), so read them as neighbourhoods on a continuum rather than
as categories.

**Stage:** exploratory. The labels are provisional, and the outputs are
illustrations, not a validated taxonomy.

## Documents

| Document | Read it for |
|---|---|
| [RESTART_HERE.md](RESTART_HERE.md) | Handoff: status, current outputs, environment, commands, caveats. **Start here.** |
| [docs/METHODS_AND_FINDINGS.md](docs/METHODS_AND_FINDINGS.md) | Article-style methods, results, limitations and next steps |
| [docs/archive/](docs/archive) | Working notes and the edition-by-edition log, kept as history |

## Code

| File | Role |
|---|---|
| [pilot.py](pilot.py) | 384-image pilot: original versus inverted negatives |
| [full_space.py](full_space.py) | Full pipeline: inventory, embeddings, PCA, k-means, t-SNE, all renders (`--render-only` reuses saved coordinates) |
| [tsne_atlas.py](tsne_atlas.py) | Exact-coordinate image atlas, display order (`PORTRAIT_FIRST_ORDER`), label loading |
| [highlight_atlas.py](highlight_atlas.py) | Adds a page highlighting a single image (for example *Le Violon d'Ingres*) |
| [clean_scatter.py](clean_scatter.py) | Text-free t-SNE dot map |
| [cluster_labels.json](cluster_labels.json) | Provisional cluster labels, tied to the reviewed coordinate hash |
| `validate_*.py`, `test_*.py` | Output validators and unit tests |

## Quick start (Windows, PowerShell)

```powershell
py -3.13 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision
& .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
& .\.venv\Scripts\python.exe -m unittest discover -s . -p "test_*.py" -v
```

The pipeline reads the scrape from `E:\PM_laptop_backup\mydocs\MR_scrape\`
(`images\` and `master.csv`). That path is the default `SOURCE` in `pilot.py`;
override it with `--source` in `pilot.py` or `full_space.py`. All
other commands are in [RESTART_HERE.md](RESTART_HERE.md).

## Not in this repository

- **Images and outputs.** Neither the source images nor the rendered outputs
  (`outputs/`) are included. Both contain collection images whose rights belong
  to the Centre Pompidou and the Man Ray estate.
- **The Python environment** (`.venv/`) and the cached model weights.
