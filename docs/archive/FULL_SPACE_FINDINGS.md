> **Archived working note.** Kept for the history of decisions. Links point to the project root; the `full_space_reordered` and `full_space_semantic` editions it mentions were deleted in the October 2026 cleanup. Current state: [RESTART_HERE.md](../../RESTART_HERE.md).

# Man Ray space: full-collection exploratory maps

## Four-page atlas edition

The [four-page atlas](../../outputs/full_space_four_page/space_tsne_image_atlas.pdf)
prepends two text-free 16:9 pages: first with no colored thumbnail outlines,
then with outlines only on reordered clusters 0-9. All images in clusters
10-15 remain present on both pages. Pages 3 and 4 retain the labeled and
fully outlined text-free views, respectively. Image pixels, positions, sizes
and draw order match across the three text-free pages; the only difference
is which thumbnail outlines are drawn.

Separate 9600 x 5400 PNGs are available for the
[unoutlined view](../../outputs/full_space_four_page/space_tsne_image_atlas_no_outlines.png)
and [clusters 0-9 view](../../outputs/full_space_four_page/space_tsne_image_atlas_clusters_00_09.png).
Earlier editions remain untouched; no fitting or source-image modification
is involved.

Validation confirms all 11,965 images on each page and identical image hashes,
positions and ordering across the text-free variants. Page 1 has zero colored
outlines; page 2 has exactly 8,541, matched to the positions and original colors
of reordered clusters 0-9; page 4 has 11,965. The two retained pages render
pixel-identically to the previous edition. Source and fitted-artifact hashes
are unchanged; nine unit tests passed and both new previews were inspected.

## Reordered edition

The preceding [two-page atlas](../../outputs/full_space_reordered/space_tsne_image_atlas.pdf)
preserves the labeled layout on page 1 and adds a text-free, maximally fitted
16:9 view on page 2. The [clean PNG](../../outputs/full_space_reordered/space_tsne_image_atlas_clean.png)
is 9600 x 5400. Uniform scaling preserves the space's shape and includes every
thumbnail; it does not stretch or crop the map to fill a widescreen rectangle.
Overlap remains intentional, with identical draw order on both pages.

The [reordered legend](../../outputs/full_space_reordered/cluster_semantic_legend.pdf)
reports counts and percentages of the 11,965 linked images:

| New ID | Provisional description | n | Percentage | Original ID |
|---|---|---:|---:|---:|
| 0 | Seated portraits / marked prints | 749 | 6.3% | 0 |
| 1 | Seated portraits / negatives | 922 | 7.7% | 4 |
| 2 | Half-length portraits / prints | 976 | 8.2% | 5 |
| 3 | Bust portraits / gestures / prints | 748 | 6.3% | 15 |
| 4 | Front-facing portraits / negatives | 1,226 | 10.2% | 6 |
| 5 | Dark-toned portrait prints | 764 | 6.4% | 1 |
| 6 | Portraits / poses / negatives | 1,211 | 10.1% | 12 |
| 7 | Full-length / fashion / costume | 507 | 4.2% | 14 |
| 8 | Interiors / people in settings | 646 | 5.4% | 8 |
| 9 | Groups / horizontal scenes | 792 | 6.6% | 9 |
| 10 | Reproductions / framed forms | 739 | 6.2% | 10 |
| 11 | Architecture / landscapes / travel | 746 | 6.2% | 11 |
| 12 | Mounted images / graphic material | 358 | 3.0% | 2 |
| 13 | Body studies / expressive poses | 588 | 4.9% | 13 |
| 14 | Objects / masks / graphic forms | 721 | 6.0% | 7 |
| 15 | Film edges / perforations | 272 | 2.3% | 3 |

Original colors, membership, positions and selected detail examples are
preserved. All presentation numbers, atlas borders/tile IDs, detail filenames
and legends use the new order. The raw coordinates retain original fit IDs;
the new display-coordinate and placement CSVs explicitly include both IDs.
Unrounded percentages and denominators are in the
[legend CSV](../../outputs/full_space_reordered/cluster_semantic_legend.csv).
The exact review-coordinate hash remains valid; no analysis was recomputed.
The earlier exports linked below are retained as the original-number edition.

Validation passed for both atlas pages: each embeds all 11,965 images; the
second page is exactly 16:9, has no PDF text, includes every thumbnail within
the page and maximizes uniform scale within the specified margins. Placement
checks allow 0.003 PDF points for nested-transform serialization (less than
0.012 output pixels). Nine unit tests passed. All counts and percentages
reconcile; the 192 detail selections, fitted artifact hashes, original JPEG
hashes and master catalog hash are unchanged. The labeled, clean and legend
previews were visually inspected; Acrobat/display review remains manual.

## Start here

- **[Exact t-SNE image atlas PDF](../../outputs/full_space_semantic/space_tsne_image_atlas.pdf)**:
  thumbnails at actual fitted positions, with a provisional semantic key.
- [Exact-atlas preview](../../outputs/full_space_semantic/space_tsne_image_atlas_preview.png)
  and [9600 x 6000 PNG](../../outputs/full_space_semantic/space_tsne_image_atlas.png).
- **[Semantic legend PDF](../../outputs/full_space_semantic/cluster_semantic_legend.pdf)**:
  all 16 groups, numbered 0-15.
- **[26-page presentation PDF](../../outputs/full_space_semantic/man_ray_space.pdf)**:
  PCA, nonlinear neighborhoods, attribution subset, metadata overlays,
  sixteen cluster detail sheets, and methodological cautions.
- **[Zoomable all-image grid atlas PDF](../../outputs/full_space_semantic/space_image_atlas.pdf)**:
  all 11,965 linked images, one tile each.
- [PCA overview PNG](../../outputs/full_space_semantic/space_pca.png).
- [Nonlinear neighborhood PNG](../../outputs/full_space_semantic/space_tsne.png).
- [Grid atlas preview PNG](../../outputs/full_space_semantic/space_image_atlas_preview.png).
- [Full grid atlas PNG](../../outputs/full_space_semantic/space_image_atlas.png):
  13,200 x 13,080 pixels.
- [Coordinates, catalog metadata, and atlas cells](../../outputs/full_space_semantic/coordinates.csv).
- [Parameters, counts, and metrics](../../outputs/full_space_semantic/summary.json).

All new page, plot, and exported thumbnail-padding backgrounds use neutral
RGB **(38, 38, 38)**, or `#262626`. Images themselves retain their original
pixels and polarity. Plot/detail PNGs are 3840 x 2160 pixels. The PDF retains
vector points and text. The exact atlas embeds thumbnails individually with
vector text and borders; the grid atlas is an image-based PDF for zooming.

The original 384-image pilot is preserved separately.

## What is "Man Ray space" here?

It is an exploratory **visual-feature space for this particular catalog scrape**,
not a claim to represent the entirety of Man Ray's practice.

Every image is represented by 512 locally computed ResNet-18 features.
Thirty-two PCA components feed the sixteen-cluster k-means grouping; the
two-dimensional presentation maps do not determine those groups.

Two views illustrate different aspects of the same features:

1. **PCA** gives a linear overview with interpretable explained-variance axes.
   PC1 accounts for 9.4% of feature variance and PC2 for 4.9%, or **14.3%
   together**. Two axes necessarily leave much of the variation off the page.
2. **t-SNE** emphasizes local neighborhoods and is more visually separated.
   Island sizes, between-island distances, and blank areas should not be
   read as historical categories or quantities.

Cluster colors and numbers are consistent between these views. Cluster IDs
are arbitrary, and are unrelated to the pilot's eight cluster numbers.

The **grid atlas** approximates the t-SNE neighborhood arrangement using recursive
spatial cuts into a 110-column by 109-row grid. Every image has a distinct
120-pixel cell; 25 cells are unused. Unlike the scatterplot, the grid displaces
images to remove overlap. Use it to navigate images, not to measure distances.
Each tile lists catalog row ID and cluster ID; the coordinates CSV links
these to titles, inventory numbers, and original filenames.

The **exact-position atlas** instead transforms the original t-SNE coordinates
by one uniform scale and translation, with the y-axis reversed for PDF/image
coordinates. No collision adjustment or grid snapping is performed. Thumbnails
retain their aspect ratio and are at most 15 PDF points across (60 pixels in
the 9600 x 6000 PNG). All 11,965 records are embedded once in a seeded,
shuffled draw order. Some are partly or wholly hidden in dense regions.
The [placement manifest](../../outputs/full_space_semantic/tsne_atlas_placements.csv)
records each center and draw order. The grid remains the complementary view
in which every image has its own unobscured tile. t-SNE scatterplots now use
equal axis scales and shared full-run limits across all overlays.

## A provisional semantic key

The run contains **16 groups numbered 0-15**. Labels were drafted from all
sixteen detail sheets (six center-near, three seeded random and three
edge examples per group), checked against catalog titles and medium counts.
They describe tendencies, not every member, and do not validate the clusters
as historical categories. No identity or gender is inferred from appearance.

| ID | Provisional description | Images |
|---|---|---:|
| 0 | Seated portraits / marked prints | 749 |
| 1 | Dark-toned portrait prints | 764 |
| 2 | Mounted images / graphic material | 358 |
| 3 | Film edges / perforations | 272 |
| 4 | Seated portraits / negatives | 922 |
| 5 | Half-length portraits / prints | 976 |
| 6 | Front-facing portraits / negatives | 1,226 |
| 7 | Objects / masks / graphic forms | 721 |
| 8 | Interiors / people in settings | 646 |
| 9 | Groups / horizontal scenes | 792 |
| 10 | Reproductions / framed forms | 739 |
| 11 | Architecture / landscapes / travel | 746 |
| 12 | Portraits / poses / negatives | 1,211 |
| 13 | Body studies / expressive poses | 588 |
| 14 | Full-length / fashion / costume | 507 |
| 15 | Bust portraits / gestures / prints | 748 |

The overlapping portrait descriptions are deliberate: medium, tone, framing,
pose and scan appearance can separate otherwise similar subjects. Mixed and
boundary examples remain visible in the detail sheets. The
[legend CSV](../../outputs/full_space_semantic/cluster_semantic_legend.csv) preserves
evidence notes, counts, exact color codes, provisional status and the reviewed
coordinate hash. This key must not be transferred to another fit's arbitrary
cluster IDs without a new review.

## Scope and exclusions

The main maps and atlas include all **11,965 catalog-linked local images**.
They are not a sample. Of these, **11,921** have an artist field exactly
equal to "Man Ray".

Forty-four other/shared artist fields remain in the full view and are
highlighted on an attribution overlay. The separate
[Man-Ray-only view](../../outputs/full_space/space_man_ray_only.png) shows the
11,921 exact-attribution records at the same fitted coordinates; it does
not fit a new space or silently classify the other records.

The 446 catalog records without downloaded files, 58 records with blank image
URLs, and local gray placeholder are accounted for in the audit tables rather
than assigned fabricated coordinates. Three byte-identical image pairs remain
as distinct catalog-linked files; no museum objects were merged.

## What the first inspection shows

The full dataset produces broad, overlapping neighborhoods rather than
sixteen sharply separate categories. The sixteen group sizes range from
272 to 1,226 images. Their sampled silhouette score is **0.059**, reinforcing
that the cluster boundaries should be treated as organizational aids.

Two illustrative detail sheets:

- [Neighborhood 3](../../outputs/full_space/neighborhood_03.png), 272 images:
  representative examples prominently show film perforations and borders,
  across different subjects. The photographed carrier is an important
  contributor to similarity.
- [Neighborhood 4](../../outputs/full_space/neighborhood_04.png), 922 images:
  displayed examples include repeated seated-portrait compositions and
  negative views, including multiple catalog-titled Yeshwant Rao Holkar
  Bahadur images. Similarity suggests avenues for catalog and close-image
  review; it does not prove a shared sitting or date.

Each detail page includes center-near examples, seeded random examples,
and more distant cluster members, not only curated successes.
The displayed examples do not validate a subject label for every member.

Medium/cluster normalized mutual information is **0.194**. Polarity,
format, digitization, composition, and subject remain entangled. Accordingly,
the full run retains original images instead of treating the pilot's
unvalidated inversion as a subject-normalization solution.

The fixed-coordinate overlays let the audience inspect how this visual
space relates to [medium](../../outputs/full_space/space_medium.png),
[catalog date bands](../../outputs/full_space/space_dates.png),
[title-derived groups](../../outputs/full_space/space_titles.png), and
[attribution](../../outputs/full_space/space_attribution.png).
Date uncertainty remains in the coordinates CSV; broad bands are not exact
capture dates. Title-derived subject flags are incomplete and overlapping
in the source; the display assigns a documented priority-based group.

## Suggested presentation sequence

1. Start with the whole image atlas at fit-to-page: make the scale tangible.
2. Show PCA as a modest linear overview, then the nonlinear neighborhood map.
3. Switch to medium colors without moving the points: expose the role of
   photographic material and catalog description.
4. Zoom into two or three neighborhoods, checking actual images and titles.
5. End with the distinction between discovery aids and established conclusions.

An appropriate framing is: **these tools make a large archive navigable and
generate questions that can be tested through close looking and catalog work**.
Do not infer sitter gender or identity from the map.

## Validation and reproducibility

- Eight unit tests passed, including exact-coordinate geometry and a full-size unique-cell assignment test,
  identical-coordinate cases, deterministic assignment, and the pilot audit tests.
- All 11,965 records have finite 512-dimensional embeddings, PCA/t-SNE
  coordinates, cluster IDs, and unique atlas cells.
- All map counts reconcile to the linked-image manifest; the attribution-only
  view contains 11,921 points.
- Specified RGB values were checked in map/detail PNG backgrounds, rendered
  presentation-page corners, and unused atlas cells.
- All 26 presentation pages and the atlas PDFs were opened and raster-rendered.
- Exact-atlas PDF placements were checked against all 11,965 recorded centers;
  every record has an embedded image and deterministic draw-order entry.
- All 16 legend labels, their counts and review/renderer hashes were checked.
- Coordinate CSV and embedding NPZ hashes are unchanged from before rendering.
- All 11,966 original JPEG hashes and the original master CSV hash were
  rechecked after processing and are unchanged.

The atlas intentionally exceeds Pillow's generic large-image warning threshold;
the validator checks its known expected dimensions and grid allocation.
The PDFs still require a manual Acrobat/presentation-display check.
The revised export is in a separate `full_space_semantic` folder because the
original grid PDF was locked during regeneration. Existing fitted artifacts
were copied byte-for-byte; PCA, t-SNE, embeddings and cluster assignments were
not recomputed.

See [full_space.py](../../full_space.py), [validate_full_space.py](../../validate_full_space.py),
and the [project guide](../../README.md) for commands. Generated outputs are persistent
on disk but ignored by Git; retain them separately with their CSV/JSON provenance.
No stronger encoder, cropping method, or human-validated taxonomy has yet
been established. Those remain the next methodological refinements.
