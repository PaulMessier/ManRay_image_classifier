# Restart here: project state and log

Read this first when resuming work. For the full methods, results, and next
steps written in article form, see [docs/METHODS_AND_FINDINGS.md](docs/METHODS_AND_FINDINGS.md).
The project overview is [README.md](README.md). The edition-by-edition log and
early working notes are archived in [docs/archive/](docs/archive).

## Status at the stopping point

- **Stage:** exploratory. The outputs are presentation illustrations, not a
  validated taxonomy.
- **Data:** 11,965 locally available Man Ray / Pompidou images embedded,
  clustered (k = 16), and mapped (t-SNE). Source images were never modified.
- **Tests:** 9 unit tests pass (`test_pilot.py`, `test_full_space.py`).
  Every output edition passed its validator when it was produced.
- **Git:** this folder is its own repository, published at
  <https://github.com/PaulMessier/ManRay_image_classifier> (branch `main`). It
  sits inside the local `ivpy` checkout but is not part of the ivpy repository.
  Only code, labels and docs are committed. `outputs/`, `.venv/` and the
  source images are git-ignored and must be backed up separately.

## Which outputs to use

All folders are under `outputs\`. All share the same coordinates (`coordinates.csv` SHA-256 begins `a8e4bddb`).

| Folder | Size | Use |
|---|---:|---|
| `full_space_highlight` | 97 MB | **Current atlas.** 5-page PDF: (1) no outlines, (2) outlines on clusters 0-9, (3) labeled atlas with legend, (4) all outlines, (5) *Le Violon d'Ingres* highlighted. |
| `full_space_clean_scatter` | small | Text-free, legend-free t-SNE dot map (PDF + 9600 x 5400 PNG), from `clean_scatter.py`. |
| `full_space_four_page` | 439 MB | **Current everything else:** presentation PDF, maps, detail sheets, legend (n and %), grid atlas, `coordinates.csv`, `summary.json`. Source for the highlight edition. |
| `full_space` | 251 MB | Original full run: embeddings, PCA, k-means, t-SNE. **Canonical computed coordinates**; all later editions are render-only reuses of this run. |
| `pilot` | 37 MB | 384-image pilot: original vs. inverted negatives. |
| `.model-cache` | 45 MB | ResNet18 weights (re-downloadable). |

Before a presentation, copy at least `full_space_highlight`,
`full_space_four_page`, and `full_space` to backup storage: none of them are
in Git.

## Chronology

1. **Repository cleanup.** Loose files in the ivpy package were moved into
   project folders; this project was one of them.
2. **Source audit.** Catalog `master.csv` (12,469 rows) linked to 11,965 of the
   11,966 local JPEGs; 446 catalog rows have no downloaded image, 58 have no URL.
3. **Pilot** (`pilot.py`). 384 stratified images. Inverting negatives did not
   materially improve organization, so originals are used throughout.
4. **Full space** (`full_space.py`). ResNet18 embeddings, 32-component PCA,
   k-means k = 16, t-SNE; 25-page presentation, maps, 16 detail sheets,
   110 x 109 grid atlas.
5. **Semantic labels and exact atlas** (`cluster_labels.json`,
   `tsne_atlas.py`). Thumbnails placed at their exact t-SNE coordinates.
6. **Portrait-first legend** (`--portrait-first`). Display order chosen by the
   user; legend shows n and %; clean 16:9 text-free page added.
7. **Four-page atlas.** Added pages without outlines and with outlines on
   display clusters 0-9 only.
8. **Highlight page** (`highlight_atlas.py`). *Le Violon d'Ingres* (record 774)
   outlined in its cluster color.
9. **Documentation** (this file, `METHODS_AND_FINDINGS.md`).
10. **Cleanup and publication (October 2026).** Deleted the superseded
    `full_space_reordered` and `full_space_semantic` editions (about 680 MB),
    moved the docs into `docs\` (working notes into `docs\archive\`), wrote a
    new README and published the code to GitHub.

## Files

| File | Role |
|---|---|
| [pilot.py](pilot.py), [test_pilot.py](test_pilot.py), [validate_outputs.py](validate_outputs.py) | Pilot pipeline, tests, validator. |
| [full_space.py](full_space.py) | Full pipeline: inventory, embeddings, PCA, k-means, t-SNE, all renders. `--render-only` reuses saved coordinates; `--portrait-first` uses the display order. |
| [tsne_atlas.py](tsne_atlas.py) | Exact-coordinate atlas; `PORTRAIT_FIRST_ORDER`, `display_clusters`, label loading, batched PDF compositing. |
| [highlight_atlas.py](highlight_atlas.py) | Appends the single-image highlight page and validates it. |
| [clean_scatter.py](clean_scatter.py) | Text-free t-SNE scatter (same points and colors as `space_tsne.png`). |
| [cluster_labels.json](cluster_labels.json) | Provisional labels and evidence notes, keyed by **original** cluster ID and bound to the reviewed coordinate hash. |
| [validate_full_space.py](validate_full_space.py), [test_full_space.py](test_full_space.py) | Output validator and unit tests. |
| [docs/METHODS_AND_FINDINGS.md](docs/METHODS_AND_FINDINGS.md) | Article-style account (methods, results, next steps). |
| [docs/archive/](docs/archive) | `EDITION_LOG.md` (the former README), `FULL_SPACE_FINDINGS.md`, `PILOT_FINDINGS.md`: historical notes. |
| [requirements.txt](requirements.txt) | Compatible version ranges (not a lock). |

## Environment

- Windows, PowerShell, from this folder.
- Interpreter: `.\.venv\Scripts\python.exe` (Python 3.13.2, created with
  `--system-site-packages`). Tested with numpy 2.2.4, pandas 2.2.3,
  Pillow 11.1.0, scikit-learn 1.6.1, matplotlib 3.10.3, PyMuPDF 1.27.2.2,
  torch 2.14.1+cpu, torchvision 0.29.1+cpu.
- The editor may not detect this venv automatically; call the executable
  explicitly or select it manually.
- Source drive must be mounted: `E:\PM_laptop_backup\mydocs\MR_scrape\`
  (`images\` and `master.csv`).

Rebuild the environment on another machine:

```powershell
py -3.13 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision
& .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

## Commands

Every script refuses to write into a nonempty output folder, so always name a
new folder.

```powershell
cd C:\Users\pm\code\ivpy\projects\Man_Ray_Pompidou_Scrape

# Tests
& .\.venv\Scripts\python.exe -m unittest discover -s . -p "test_*.py" -v

# Full recomputation (embeddings + PCA + k-means + t-SNE + renders)
& .\.venv\Scripts\python.exe .\full_space.py --output .\outputs\full_space_repeat
& .\.venv\Scripts\python.exe .\validate_full_space.py .\outputs\full_space_repeat

# Re-render current editions from the saved coordinates (about 5-8 minutes)
& .\.venv\Scripts\python.exe .\full_space.py --render-only --portrait-first --output .\outputs\full_space_new
& .\.venv\Scripts\python.exe .\validate_full_space.py .\outputs\full_space_new

# Add the highlight page for any catalog image URL
& .\.venv\Scripts\python.exe .\highlight_atlas.py --source .\outputs\full_space_four_page --output .\outputs\full_space_highlight_new --image-url "https://www.centrepompidou.fr/media/picture/81/4b/814bf1488065a6225ef18dfb56cc6251/thumb_medium.jpg"

# Pilot
& .\.venv\Scripts\python.exe .\pilot.py --output .\outputs\pilot_repeat
& .\.venv\Scripts\python.exe .\validate_outputs.py .\outputs\pilot_repeat
```

## Caveats when resuming

- **Labels are tied to the coordinates.** A full recomputation produces new
  cluster IDs; the pipeline then withholds the labels and warns. Review new
  detail sheets and write a new `cluster_labels.json` before reusing labels.
- **Two numbering systems.** `cluster_labels.json` and `coordinates.csv` use
  original k-means IDs; legends, presentation, and `display_coordinates.csv`
  use display IDs. The mapping
  is `PORTRAIT_FIRST_ORDER` in [tsne_atlas.py](tsne_atlas.py) and the table in
  [docs/METHODS_AND_FINDINGS.md](docs/METHODS_AND_FINDINGS.md).
- **Acrobat locks open PDFs.** Close them before re-rendering, or write to a
  new folder.
- **Large files.** The grid PNG (172.6 MP) triggers Pillow's
  DecompressionBomb warning; this is expected.
- **Validator assumption.** `validate_full_space.py` expects 11,921 records in
  the Man-Ray-only subset; update it if the source changes.
- **Not yet done:** a manual Acrobat review of the final PDFs, and image rights
  or credit clearance for public display.

## Suggested first task when resuming

Pick one item from section 7 of
[docs/METHODS_AND_FINDINGS.md](docs/METHODS_AND_FINDINGS.md). The cheapest high-value
step is a **cluster-stability check** (several seeds and k values). The most
interesting is **negative-to-print matching**.
