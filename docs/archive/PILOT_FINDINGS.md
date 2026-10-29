> **Archived working note.** Kept for the history of decisions. Links point to the project root; the `full_space_reordered` and `full_space_semantic` editions it mentions were deleted in the October 2026 cleanup. Current state: [RESTART_HERE.md](../../RESTART_HERE.md).

# Pilot findings: October 17, 2026

## Full-scale exploratory continuation

The original-image baseline has been extended to the full linked collection.
See the [project guide](../../README.md#full-collection-man-ray-space) for PCA,
nonlinear neighborhood maps, catalog overlays, and an all-image atlas on
RGB (38, 38, 38) backgrounds. The pilot figures below remain unchanged.
This scale-up does not imply that stronger encoders, border handling, or
the methodological refinements proposed here have already been validated.

## Open these first

- [Presentation PDF](../../outputs/pilot/pilot_presentation.pdf): 15 landscape pages,
  including coverage, original/positive-view maps, date and title overlays,
  polarity examples, eight cluster detail sheets, and limitations.
- [Pilot image atlas PDF](../../outputs/pilot/pilot_atlas.pdf): one zoomable page
  containing all 384 selected images, sorted into cluster blocks.
- [Pilot image atlas PNG](../../outputs/pilot/pilot_atlas.png): 3840 x 2660 pixels.
- [Original map](../../outputs/pilot/map_original.png) and
  [positive-view map](../../outputs/pilot/map_positive_view.png): 3200 x 1800 PNGs.
- [Date and title overlays](../../outputs/pilot/map_catalog_overlays.png):
  the same positive-view layout with different metadata colors.
- [Numerical results and provenance](../../outputs/pilot/summary.json).

The atlas is **not** a similarity-preserving spatial layout: it is sorted by
cluster for inspection. Original thumbnails are shown even when cluster
selection used positive-view embeddings. Image IDs correspond to catalog-row
`record_id` in [pilot_coordinates.csv](../../outputs/pilot/pilot_coordinates.csv).

These deliverables cover a pilot sample, not all 11,965 linked local images.
Their PDF and PNG sizes are appropriate for an initial presentation review;
individual source images still have only about 500 pixels on the long edge.

## What was done

1. Audited all 11,966 local JPEGs, including dimensions, decoding, and SHA-256.
2. Joined the 12,469 catalog rows to local filenames and recorded every
   missing URL, missing image, and unmatched local file.
3. Identified three byte-identical pairs, preserving all source copies.
4. Selected 384 distinct records using seeded round-robin sampling across
   medium x date band x title-derived subject strata. This deliberately
   oversamples rare strata; percentages in this sample are **not collection
   prevalence estimates**.
5. Computed 512-dimensional pooled ResNet-18 ImageNet embeddings locally.
   Frames were letterboxed rather than center-cropped. No captions or
   museum labels were used as inputs to the embedding model.
6. Recomputed embeddings for the 156 catalog-labeled negatives after simple
   RGB inversion. Other images retained exactly the same embeddings.
7. Used 32 PCA components and eight-cluster k-means for each representation,
   with t-SNE only for display. Eight is a pilot setting, not a discovered
   number of natural categories.

The sample contains 156 negative, 128 print, and 100 other/unknown media
records; 382 artist fields are exactly Man Ray and two are Constantin Brancusi.
The latter remain identifiable in the data rather than being relabeled.

## First visual observations

Inspection of representative, random, and cluster-edge examples suggests
several useful avenues:

- [Cluster 3](../../outputs/pilot/cluster_3.png) brings together many portrait
  compositions, including profile views, seated figures, and paired images.
- [Cluster 4](../../outputs/pilot/cluster_4.png) includes a concentration of body
  studies, but its edge cases show that it is not a clean subject classifier.
- [Cluster 0](../../outputs/pilot/cluster_0.png) includes object studies, masks,
  reproductions, and photogram-like compositions.
- [Cluster 5](../../outputs/pilot/cluster_5.png) contains several reproductions of
  artwork and graphic material, with heterogeneous edge cases.
- [Cluster 6](../../outputs/pilot/cluster_6.png) prominently groups images with
  film perforations. This is an important warning: the embedding can recognize
  the photographic carrier or digitization framing rather than the subject.

These are observations of displayed examples, not validated labels for every
cluster member. They do not establish identities, sitting dates, process
histories, or intent. In particular, do not convert the portrait neighborhoods
into male/female labels based on appearance.

## Polarity comparison: inversion did not solve the medium effect

| Diagnostic | Originals | Inverted-negative variant |
|---|---:|---:|
| Same catalog medium among ten nearest neighbors | 53.8% | 58.7% |
| Chance same-medium expectation for this sample | 34.2% | 34.2% |
| Cluster/medium normalized mutual information | 0.141 | 0.147 |
| Silhouette in PCA clustering space | 0.091 | 0.090 |

An average 60.0% of each image's ten neighbors remained the same between the
two representations. Inversion changes neighborhoods substantially, but it
does **not** reduce same-medium association on these diagnostics.

This is not proof that inversion is universally unhelpful: medium and subject
may genuinely correlate, and the sample intentionally changes medium
proportions. It does mean that the positive-view variant cannot be described
as a validated subject-normalization improvement.

The low silhouette values and mixed boundary examples also argue against
presenting the eight groups as sharply separated natural classes.

## Duplicate review

The [duplicate review table](../../outputs/pilot/duplicate_review.csv) retains hashes,
filenames, titles, inventory numbers, and catalog IDs.

- Records 759 and 761 share inventory `AM 1994-394 (2319)` and identical bytes.
- Records 3645 and 3768 share inventory `AM 1994-394 (2)` and identical bytes.
- Records 5874 and 6774 have different inventory numbers, `AM 1994-394 (4269)`
  and `AM 1994-394 (4267)`, but identical downloaded bytes.

The first two may reflect catalog/scrape duplication, while the third needs
museum-record review. Identical downloaded thumbnails are not sufficient
evidence that two collection objects are the same. No originals were deleted.

## Recommended next development stage

Proceed with **a navigable atlas and carefully captioned detail neighborhoods**,
not automatic demographic classification. Before a definitive full run:

1. Review the polarity examples and identify catalog-medium/image-polarity
   disagreements or ambiguous processes.
2. Compare a stronger visual encoder with this baseline and test a conservative,
   explicitly recorded border-cropping variant. Keep the full-frame baseline:
   carrier information may itself be historically interesting.
3. Manually annotate a small held-out review set for broad visible subjects
   and carrier/border effects. Evaluate neighborhood usefulness, not just
   prettier map islands.
4. Compare cluster counts and an unassigned/noise-capable clustering baseline.
5. Select the representation based on that review, then build the all-image
   scatterplot, collision-free atlas, and presentation detail pages.

The immediate message supported by the pilot is that image computation can
organize a heterogeneous archive into inspectable neighborhoods, while also
revealing how subject matter, material format, and digitization conventions
become entangled.

## Validation performed

- Five focused unit tests passed: URL matching, metadata labels/date bands,
  deterministic sampling, non-destructive inversion/full-frame handling, and
  audit coverage including missing/unmatched/duplicate fixtures.
- Dependency consistency check passed in the project environment.
- All 11,966 source JPEG hashes and the master catalog hash were rechecked
  after the run; originals are unchanged.
- All 384 sample records have finite embeddings, coordinates, cluster labels,
  and atlas allocations; nonnegative embeddings are unchanged between variants.
- All 15 presentation pages and the one-page atlas PDF were opened and
  raster-rendered with PyMuPDF; PDF text and selected page previews were checked.
- Editor diagnostics reported no errors in the three Python files.

The PDFs have **not** been reviewed in Acrobat on the eventual presentation
display. That remains a delivery check, particularly for font size and zoom.
Use [validate_outputs.py](../../validate_outputs.py) to repeat artifact and source
integrity checks; it intentionally requires the external source drive.
