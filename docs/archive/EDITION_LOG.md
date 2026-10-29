> **Archived working note.** Kept for the history of decisions. Links point to the project root; the `full_space_reordered` and `full_space_semantic` editions it mentions were deleted in the October 2026 cleanup. Current state: [RESTART_HERE.md](../../RESTART_HERE.md).

# Man Ray / Centre Pompidou collection analysis

## Purpose

Develop presentation graphics demonstrating how computational tools can make
a large photographic collection navigable and reveal patterns relevant to
artistic practice. The overview should include every eligible image, with
detail views that let the audience inspect what the groupings actually contain.

The corrected folder name is `Man_Ray_Pompidou_Scrape`.
This project analyzes an existing scrape; it does not download collection images.

**Resuming work?** Start with [RESTART_HERE.md](../../RESTART_HERE.md) (status,
canonical outputs, commands, caveats). The full article-style account of
methods, models, results, limitations, and next steps is
[METHODS_AND_FINDINGS.md](../METHODS_AND_FINDINGS.md).

## Clean t-SNE scatter

[space_tsne_clean.pdf](../../outputs/full_space_clean_scatter/space_tsne_clean.pdf)
(vector, 16:9) and a [9600 x 5400 PNG](../../outputs/full_space_clean_scatter/space_tsne_clean.png)
show the same points and colors as `space_tsne.png` with no title, legend,
cluster numbers, frame, or footer, scaled to fill the page. Rendered by
[clean_scatter.py](../../clean_scatter.py) from
`outputs\full_space_four_page\display_coordinates.csv`; no refitting.

```powershell
& .\.venv\Scripts\python.exe .\clean_scatter.py --output .\outputs\full_space_clean_scatter_repeat
```

## Single-image highlight edition

The **[five-page atlas PDF](../../outputs/full_space_highlight/space_tsne_image_atlas.pdf)**
retains the four-page edition and appends a fifth, text-free 16:9 page with
exactly one colored outline: **Le Violon d'Ingres**, 1924, inventory
**AM 1993-117**, catalog row ID **774**. The URL identifies the file
`81_4b_814bf1488065a6225ef18dfb56cc6251.jpg` uniquely.

The outline uses its reordered cluster **14** color, `#ff9896`, and a
1.5-point stroke for visibility. It is drawn above the montage so overlapping
images cannot hide the locator. No image is moved or redrawn; original
overlap remains. All other thumbnails have no added borders.

- [Highlighted page PNG, 9600 x 5400](../../outputs/full_space_highlight/space_tsne_image_atlas_highlight.png)
  and [preview](../../outputs/full_space_highlight/space_tsne_image_atlas_highlight_preview.png).
- [Highlight provenance and validation](../../outputs/full_space_highlight/highlight_summary.json).

[highlight_atlas.py](../../highlight_atlas.py) appends the page from the borderless
first page of the four-page edition, checks the unique catalog URL and recorded
position, and validates all 11,965 embedded images, the single outline and
pixel-identical retention of the first four pages. Earlier exports are not
modified.

```powershell
& .\.venv\Scripts\python.exe .\highlight_atlas.py --source .\outputs\full_space_four_page --output .\outputs\full_space_highlight_repeat --image-url "https://www.centrepompidou.fr/media/picture/81/4b/814bf1488065a6225ef18dfb56cc6251/thumb_medium.jpg"
```

## Four-page atlas edition

The **[four-page atlas PDF](../../outputs/full_space_four_page/space_tsne_image_atlas.pdf)**
adds two opening pages, using the same text-free 16:9 layout:

1. **No colored outlines** on any thumbnail.
2. **Colored outlines on clusters 0-9 only**, using the reordered IDs below;
   images in clusters 10-15 remain visible without outlines.
3. The existing labeled atlas, including counts and percentages.
4. The existing text-free atlas with outlines on all clusters.

The first, second and fourth pages have identical image positions, sizes,
pixels and draw order. Outlines are composed immediately after each thumbnail,
so later images occlude earlier outlines just as in the original atlas.
There are no added text or legends on these three pages. The RGB (38,38,38)
background and entire image space are retained.

- [No-outlines PNG, 9600 x 5400](../../outputs/full_space_four_page/space_tsne_image_atlas_no_outlines.png)
  and [preview](../../outputs/full_space_four_page/space_tsne_image_atlas_no_outlines_preview.png).
- [Clusters 0-9 PNG, 9600 x 5400](../../outputs/full_space_four_page/space_tsne_image_atlas_clusters_00_09.png)
  and [preview](../../outputs/full_space_four_page/space_tsne_image_atlas_clusters_00_09_preview.png).
- [Full four-page export folder](../../outputs/full_space_four_page), with its
  coordinates, placement manifest, summary, legends and other presentation files.

Earlier two-page editions remain unchanged. To regenerate the four-page set:

```powershell
& .\.venv\Scripts\python.exe .\full_space.py --render-only --portrait-first --output .\outputs\full_space_four_page
& .\.venv\Scripts\python.exe .\validate_full_space.py .\outputs\full_space_four_page
```

## Reordered presentation export

The preceding two-page set is in [outputs/full_space_reordered](../../outputs/full_space_reordered).
Earlier exports remain unchanged.

- **[Two-page exact t-SNE atlas PDF](../../outputs/full_space_reordered/space_tsne_image_atlas.pdf)**:
  page 1 retains the labeled layout; page 2 contains only the image space on
  a 16:9 field, without titles, legends, footnotes or other added text.
- [Labeled atlas PNG](../../outputs/full_space_reordered/space_tsne_image_atlas.png),
  9600 x 6000; [preview](../../outputs/full_space_reordered/space_tsne_image_atlas_preview.png).
- **[Text-free atlas PNG](../../outputs/full_space_reordered/space_tsne_image_atlas_clean.png)**,
  9600 x 5400; [preview](../../outputs/full_space_reordered/space_tsne_image_atlas_clean_preview.png).
- **[Reordered legend PDF](../../outputs/full_space_reordered/cluster_semantic_legend.pdf)**,
  [PNG](../../outputs/full_space_reordered/cluster_semantic_legend.png), and
  [CSV](../../outputs/full_space_reordered/cluster_semantic_legend.csv):
  every group has its count and percentage of all 11,965 linked images.
- [Updated presentation PDF](../../outputs/full_space_reordered/man_ray_space.pdf)
  and [non-overlapping grid atlas PDF](../../outputs/full_space_reordered/space_image_atlas.pdf).

The requested order is applied consistently to atlas/plot legends, map
numbers, detail sheets and grid tile IDs. Existing group colors stay with
their original memberships. No embeddings, coordinates or groups are refitted.
The clean atlas uses the largest uniform fit within a 12-point margin, retaining
the entire space, image aspect ratios, overlap and drawing order. The space
is not stretched to fill the wider screen; unused side space is intentional.
Both pages retain the RGB (38,38,38) background.

The original [coordinates CSV](../../outputs/full_space_reordered/coordinates.csv)
retains the fitted cluster IDs for provenance.
[Display coordinates](../../outputs/full_space_reordered/display_coordinates.csv),
the legend CSV and [placement manifest](../../outputs/full_space_reordered/tsne_atlas_placements.csv)
include both the new `cluster` ID and `original_cluster`.
The summary records the display-to-original mapping. Detail examples remain
the same as before renumbering. Percentages are displayed to one decimal
place; rounding may prevent displayed values from summing to exactly 100%.
The Man-Ray-only map uses its displayed subset of 11,921 as its percentage
denominator; all-collection legends use 11,965.

To regenerate this set, close its PDFs in Acrobat first:

```powershell
& .\.venv\Scripts\python.exe .\full_space.py --render-only --portrait-first --output .\outputs\full_space_reordered
& .\.venv\Scripts\python.exe .\validate_full_space.py .\outputs\full_space_reordered
```

## Full-collection "Man Ray space"

The completed run and a suggested presentation sequence are described in
[FULL_SPACE_FINDINGS.md](FULL_SPACE_FINDINGS.md).

The [full-scale mapping script](../../full_space.py) extends the original-image
baseline to every linked image, with a neutral RGB **(38, 38, 38)** export
background. The original pilot remains separate and is not recolored.

Full-run deliverables:

- **[Exact t-SNE image atlas PDF](../../outputs/full_space_semantic/space_tsne_image_atlas.pdf)**:
  all 11,965 thumbnails centered at the actual fitted coordinates, with a
  semantic legend. Individual thumbnail images and text remain embedded in
  the PDF for zooming. Dense regions overlap; not every image is visible.
- [Exact-atlas preview](../../outputs/full_space_semantic/space_tsne_image_atlas_preview.png)
  and [9600 x 6000 PNG](../../outputs/full_space_semantic/space_tsne_image_atlas.png).
- **[Provisional semantic legend PDF](../../outputs/full_space_semantic/cluster_semantic_legend.pdf)**,
  [PNG](../../outputs/full_space_semantic/cluster_semantic_legend.png), and
  [CSV with evidence, counts, colors and coordinate hash](../../outputs/full_space_semantic/cluster_semantic_legend.csv).
- [Updated 26-page presentation PDF](../../outputs/full_space_semantic/man_ray_space.pdf): PCA, nonlinear
  neighborhood maps, catalog overlays, attribution subset, and cluster details.
- [Spatial image atlas PDF](../../outputs/full_space_semantic/space_image_atlas.pdf): every
  linked image in its own tile, arranged approximately by neighborhood.
- [PCA PNG](../../outputs/full_space_semantic/space_pca.png),
  [neighborhood-map PNG](../../outputs/full_space_semantic/space_tsne.png), and
  [grid-atlas preview](../../outputs/full_space_semantic/space_image_atlas_preview.png).
- [Coordinates and catalog linkage](../../outputs/full_space_semantic/coordinates.csv).
- [Exact thumbnail placements and draw order](../../outputs/full_space_semantic/tsne_atlas_placements.csv).
- [Run parameters and metrics](../../outputs/full_space_semantic/summary.json).

The revised export uses a separate folder because the original grid PDF was
locked during rendering, likely by a viewer. No fitting was repeated.
There are **16 clusters numbered 0-15**, not 15 clusters.

```powershell
$env:LOKY_MAX_CPU_COUNT = "4"
& .\.venv\Scripts\python.exe .\full_space.py --output .\outputs\full_space_repeat
& .\.venv\Scripts\python.exe .\validate_full_space.py .\outputs\full_space_repeat
```

The full run uses original images, not inverted negatives: the pilot did not
validate inversion as an improvement. It reuses ResNet-18 embeddings as an
explicit baseline rather than implying a stronger model has been tested.
Full-frame letterboxing during feature extraction remains gray 128 to preserve
the pilot baseline; **exported** thumbnail padding and page backgrounds use
gray 38. Source-image pixels are never recolored.

Sixteen-cluster k-means is fitted in 32-dimensional PCA space. PCA's first two
axes provide an explained-variance overview; t-SNE provides a separate,
nonlinear neighborhood view. Neither visual map is used as the clustering
input. The atlas uses recursive spatial cuts to allocate distinct grid cells:
it preserves approximate neighborhoods but displaces the fitted coordinates.
The additional exact-position atlas uses a uniform scale, translation and
y-axis reversal, without grid displacement. Its seeded drawing order is
recorded: every record is embedded once, but overlapping thumbnails can hide
one another. Use the grid version to inspect every tile. Scatterplots use
equal axis scales so their shape matches the exact-coordinate atlas.

Semantic names describe tendencies seen in the 12-image detail sheets for
each group, cross-checked against catalog titles and medium counts. They are
not an automatic subject classification or a validated taxonomy. Several
portrait groups differ in medium, tone, framing and pose rather than subject.
[cluster_labels.json](../../cluster_labels.json) records the evidence basis;
[tsne_atlas.py](../../tsne_atlas.py) binds this review to the current coordinate-file
SHA-256. A different run emits a warning and withholds semantic descriptions
until its cluster IDs have been reviewed, rather than reusing arbitrary IDs.

All linked records remain in the overview, including other/shared artist
fields. A separate Man-Ray-exact-attribution view uses the same fitted
coordinates rather than fitting a different space. This makes the scope
explicit without hiding catalog exceptions.

The script refuses to overwrite a nonempty output folder. `--render-only`
can intentionally regenerate exports from existing coordinates without
recomputing embeddings. Generated outputs remain excluded from Git.

To regenerate the revised set from its retained coordinates (close its PDFs
in Acrobat first):

```powershell
& .\.venv\Scripts\python.exe .\full_space.py --render-only --output .\outputs\full_space_semantic
& .\.venv\Scripts\python.exe -m unittest discover -s . -p test_*.py -v
& .\.venv\Scripts\python.exe .\validate_full_space.py .\outputs\full_space_semantic
```

## Completed pilot

A 384-image local pilot has been run. Start with the [pilot findings](PILOT_FINDINGS.md),
the [15-page presentation PDF](../../outputs/pilot/pilot_presentation.pdf), or the
[all-pilot-image atlas PDF](../../outputs/pilot/pilot_atlas.pdf). These are exploratory
sample outputs, **not the full-collection visualization**.

The [implementation](../../pilot.py) audits every local image and catalog record,
selects a deterministic coverage sample, computes local ResNet-18 embeddings,
and compares originals with inverted previews of catalog-labeled negatives.
It produces maps, metadata overlays, cluster details, and a tile for every
sampled image. No facial identity or gender inference is performed.

### Reproducing the pilot

Run from this project folder in PowerShell:

```powershell
& .\.venv\Scripts\python.exe .\pilot.py --output .\outputs\pilot_repeat
& .\.venv\Scripts\python.exe -m unittest discover -s . -p test_pilot.py -v
& .\.venv\Scripts\python.exe .\validate_outputs.py .\outputs\pilot_repeat
```

The script refuses to overwrite a nonempty output folder. Use `--source` for
a different source root and `--sample-size` for a different pilot size.
The default seed is 20261017. Preserve outputs and their manifest together.

The project `.venv` was created with `--system-site-packages` to reuse the
already installed scientific packages; PyTorch and Torchvision were installed
inside that environment from the official CPU wheel index. It does not change
the repository's older virtual environments. The editor may require manual
selection of this project's `.venv\Scripts\python.exe`.

For a clean environment on another machine:

```powershell
py -3.13 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision
& .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

The initial run downloads ResNet-18 weights from the PyTorch model host;
collection images remain local. The model weights are cached beneath
`outputs\.model-cache`. [summary.json](../../outputs/pilot/summary.json) records
tested package versions, the weight hash, source/catalog hashes, model and
preprocessing details, seed, and metrics. The requirements file defines broad
compatible ranges, not an exact environment lock.

Generated `outputs` are ignored by Git because they contain image derivatives,
large reports, model weights, and machine-specific paths. Source, tests, and
findings remain trackable. Back up or distribute deliverables separately.

## Source material

Originals remain external and unchanged:

- Images: `E:\PM_laptop_backup\mydocs\MR_scrape\images`
- Catalog: `E:\PM_laptop_backup\mydocs\MR_scrape\master.csv`
- Spreadsheet: `E:\PM_laptop_backup\mydocs\MR_scrape\master.xlsx`
- Four dated scrape CSVs alongside the master catalog.

Inspection on October 17, 2026 used the master CSV, local filenames, all image
headers, SHA-256 hashes, and an evenly spaced filename sample of 60 images.
The spreadsheet was not compared to the CSV. The visual sample is not a
statistical estimate of subject prevalence.

### Verified inventory

| Measure | Result |
|---|---:|
| Local JPEG files | 11,966 |
| Total image size | Approximately 0.215 GiB |
| Catalog rows | 12,469 |
| Rows linked to local images | 11,965 |
| Unique linked local images | 11,965 |
| Catalog rows without a local match | 504 |
| Missing matches with blank image URL | 58 |
| Missing matches with nonblank image URL | 446 |
| Unmatched local image | `blank.jpg`, visually a gray placeholder |
| Linked records attributed exactly to Man Ray | 11,921 |
| Linked records with other artist fields | 44 |
| Linked records whose medium contains "Negatif" with the catalog's accent | 6,659 |
| Linked records whose medium starts with "Epreuve" | 4,761 |
| Other or unspecified linked media | 545 |
| Longest edge of 500 pixels | 11,964 files |
| Other longest edges | One 489-pixel file; one 492-pixel file |
| Image-header/decode failures encountered | 0 |
| Byte-identical duplicate groups | 3 pairs, or 3 extra copies |

The metadata contains `img`, `title`, `artist`, `date`, `domain`, `dims`,
`medium`, `ondisplay`, and `inv`. Local filenames can be derived from the image
URL's two prefix directories and image identifier:

```text
.../picture/18/a9/18a90e1d0612fa1ccf3b7fcbaba72434/thumb_medium.jpg
    -> 18_a9_18a90e1d0612fa1ccf3b7fcbaba72434.jpg
```

All 12,411 nonblank master image URLs are unique. The three byte-duplicate pairs
therefore require separate review: distinct image identifiers can have identical
downloaded pixels. Do not automatically merge distinct museum objects.

The master includes 52 artist fields other than exactly "Man Ray"; 44 of those
records have local images. Do not silently present them as Man Ray works.
For an all-files overview, show the 11,965 linked images and flag attribution;
provide an explicit Man-Ray-only view of 11,921 records where appropriate.
Report the placeholder and missing images separately, rather than inventing
coordinates or silently omitting them.

### What the images suggest

The inspected sample includes portraits, groups, architecture, landscapes,
objects, reproductions, both negatives and positives, and visible film edges
and borders. These are possible avenues of analysis, not established clusters.

Nearly all sources are catalog thumbnails. Their resolution is adequate for
small montage tiles and a pilot embedding analysis, but not for detailed
full-screen enlargement of individual photographs.

## Recommended presentation: scale, structure, evidence

### 1. All-image collection map

Use locally computed image embeddings, a two-dimensional layout, and a separate
cluster analysis to produce:

- A clean vector scatterplot with one mark per linked image and cluster colors.
- A companion image atlas with one small thumbnail per linked image, arranged
  near its map neighborhood using collision avoidance or a grid assignment.
- Counts for each cluster, an explicit unassigned/noise category, and coverage
  figures explaining what is and is not represented.

The scatterplot preserves layout coordinates; a grid atlas necessarily moves
images to make them visible. Explain that distinction. Verify the exported
point and tile counts against the manifest: no sampling away inconvenient
records, overwritten tiles, or hidden decoding failures.

A flat grid of around 110 by 109 cells has room for all 11,965 images. At
100-pixel cells, that is roughly an 11,000-pixel-square raster atlas. A
similarity-preserving grid or a clustered block atlas is often more legible
for a talk than thousands of overlapping thumbnails.

### 2. Cluster detail sheets

For a manageable set of visually coherent groups, show:

- Representative images selected as medoids or nearest neighbors of a cluster
  center, not only the most attractive examples.
- A small random sample and some boundary cases, to expose heterogeneity.
- Cluster size, catalog-title examples, media distribution, and available dates.
- Optional linked negative/positive or near-duplicate examples where verified.

Possible interpretive themes include repetition within sittings, viewpoint and
framing, recurring compositions, studio versus exterior work, and the relation
between prints, negatives, and reproductions. A cluster suggests a question;
it does not by itself establish a sitting, an identity, or artistic intention.

### 3. Same map, different metadata overlays

Keep coordinates fixed and recolor by:

1. Negative / print / other or unknown catalog medium.
2. Date or broad date interval, preserving uncertainty.
3. Catalog-supported subject flags such as portrait, unidentified person,
   fashion, landscape, or reproduction.
4. Artist attribution and missing/uncertain metadata, as audit layers.

This is particularly persuasive for a presentation: the visual organization
stays fixed while the audience sees how different aspects of the archive
relate to it. Do not recluster separately for every overlay and imply that
the resulting positions are directly comparable.

## Approaches ranked by usefulness

| Approach | Strength | Limitation | Recommendation |
|---|---|---|---|
| Catalog-led overview | Immediate evidence on media, dates, titles, attribution, and coverage | Catalog terms are uneven; titles are not a complete subject ontology | Start here and retain as an independent baseline |
| General visual embeddings plus clustering | Finds composition and subject neighborhoods across the entire set | May group polarity, borders, and scan appearance instead of subject | Main experimental approach, with sensitivity checks |
| Local image/text embedding similarity | Helps test candidate descriptions such as portrait, landscape, or object study | Prompt-dependent similarity is not a calibrated classification probability | Use as an aid to human labeling, not ground truth |
| Near-duplicate and repetition search | Could reveal variants, repeated compositions, or different representations of one image | Visual similarity does not prove identical objects or shared sessions | Strong candidate for a focused detail graphic |
| Basic tone, aspect ratio, edge, and texture features | Interpretable baseline for format and digitization patterns | Likely less informative about subject matter | Diagnostic comparison, not the sole semantic analysis |

Examples of model families worth a pilot are DINO-style visual embeddings and
CLIP-style image/text embeddings. Choose one baseline first; no particular
model, weights, hardware requirement, or dependency versions are prescribed
until the environment and a small pilot have been checked.

Image processing and inference should run locally. No images need to be sent
to an external service. Downloading model weights, if needed, is a separate
explicit setup step, subject to license review.

## Portraits and the proposed male/female grouping

Portrait versus non-portrait is a useful starting question, but retain group
portraits, bodies/fragments, ambiguous cases, and unknowns rather than forcing
every image into a binary.

The catalog offers a better-supported starting point than appearance-based
gender inference. Among linked records, case-insensitive title searches found:

- 704 containing `portrait`.
- 2,616 matching `personne.*non identifi`.
- 457 containing `femme`.
- 191 containing `homme`.
- 81 containing `rayograph`.
- 118 containing `mode`.
- 74 containing `paysage`.
- 400 containing `reproduction`.

These are overlapping substring/regex flags, not mutually exclusive classes
or validated counts of depicted people. Many named portraits do not contain
the word "portrait"; many unidentified-person records lack gender terms.

For any gender-related presentation, use explicit catalog wording or reviewed,
documented biographical metadata, with unknown and ambiguous categories.
Do not assign a person's gender from facial appearance. Describe a title-based
result as a pattern in catalog description, not a complete census of sitters.
Named sitter titles may support recurrence studies after manual title review;
face recognition is not necessary for the proposed presentation.

## The central methodological issue: negatives and positives

There are enough catalog-labeled negatives for polarity to dominate the map.
That could be an interesting material-history observation, but it would be
misleading to label it a subject discovery.

For a pilot:

1. Retain original files and catalog medium labels.
2. Compute a baseline representation of original images.
3. For catalog-labeled negatives, derive temporary positive-view previews and
   test an alternative subject-oriented representation. Use an explicit
   unknown category when medium is absent or ambiguous.
4. Compare representative neighborhoods, cluster membership, and separation
   by medium between the two representations.
5. Compare full-frame and cautiously cropped views to assess film edges,
   borders, annotations, and backgrounds. Never overwrite originals or crop
   them silently.

Simple digital inversion is a viewing transformation, not a reconstruction of
Man Ray's intended print. Tinted supports, contact sheets, solarization, and
other processes can make it misleading. Inspect examples before applying it
collection-wide. Catalog media can also describe the object rather than the
exact visible polarity of its web reproduction.

Cluster in the higher-dimensional representation, optionally after PCA, not
only in the two-dimensional presentation layout. A UMAP-like layout can help
navigation but can create apparent islands; it is not evidence of discrete
historical categories. Review a density-based method with noise alongside
a simple k-means baseline, using stable seeds and neighborhood checks.

## Acrobat-ready deliverables

Recommended set:

- Landscape 16:9 presentation PDF: vector overview points, readable labels,
  coverage note, metadata overlays, and cluster detail pages.
- A separate large-page, zoomable atlas PDF containing every eligible image.
- High-resolution PNG companions for convenient insertion into other slides.
- A machine-readable manifest linking every plotted item to its filename,
  catalog inventory number, coordinates, cluster, and processing status.
- A short methods/limitations page and an excluded-or-missing-record table.

Keep points, labels, and legends vector where possible; embed fonts. Tile image
resolution and PDF compression should be chosen for the intended screen and
zoom level, rather than using an arbitrary high DPI value. A large square atlas
can be approximately 11,000-12,000 pixels across, while ordinary 16:9 slides
can have roughly 4,000-pixel-wide raster companions if needed.

Upsampling cannot recover detail absent from the approximately 500-pixel
originals. Obtain higher-resolution source images only if needed and permitted;
record museum credit and reuse terms before public distribution.

Before delivery, open PDFs in Acrobat, inspect fit-to-page and deep zoom, check
font rendering, count all plotted items, and confirm that detail images remain
legible at the actual presentation size.

## Proposed next step

The initial plan below has now been exercised by the pilot. See
[PILOT_FINDINGS.md](PILOT_FINDINGS.md) for measured results and the recommended
next development stage before a full-collection run:

1. Create an image/catalog manifest and missing-file report.
2. Review the three byte-identical pairs without deleting source files.
3. Choose a stratified sample spanning catalog media, date ranges, named and
   unidentified titles, and broad visual subjects; include a random component.
4. Compare original and polarity-aware embeddings and inspect neighborhoods.
5. Decide whether subject, format/process, or repetition gives the strongest
   interpretable presentation, then process every eligible image.

Do not treat fuzzy dates as exact capture years: "vers 1930" alone occurs
3,163 times in the full master catalog. Catalog date conventions, survival,
accession history, and the scrape's missing images all limit historical claims.

The presentation's strongest defensible message is that computation creates
a navigable overview and testable questions at collection scale, while close
inspection and catalog evidence remain necessary to interpret the patterns.
