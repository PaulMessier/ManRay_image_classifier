# Mapping a photographic oeuvre at scale: an exploratory visual-embedding analysis of 11,965 Man Ray images from the Centre Pompidou catalog

*Working paper, exploratory stage. Prepared as documentation for presentation
graphics; not peer reviewed. Operational details for resuming work are in
[RESTART_HERE.md](../RESTART_HERE.md).*

## Abstract

Photographic collections are often far larger than any viewer can survey by
eye. This project tests whether a standard, off-the-shelf computer-vision model
can organize nearly twelve thousand Man Ray images scraped from the Centre
Pompidou online catalog into a navigable "Man Ray space," and whether that
organization surfaces patterns relevant to artistic practice. Each image was
represented by a 512-dimensional feature vector from an ImageNet-trained
ResNet18 network. The vectors were reduced with principal component analysis
(32 components, 56.1% of variance), partitioned with k-means into 16 clusters,
and projected into two dimensions with t-SNE. The full collection was rendered
as an image atlas in which every thumbnail sits at its t-SNE position, with
semantic cluster labels drafted from systematic inspection of sample sheets.
The strongest organizing factor was **material state**: negatives and prints
separate sharply, even within the same subject (cluster-medium normalized
mutual information 0.194; six of the sixteen clusters are 93-98% one medium).
Within that division the space organizes by **portrait framing** (seated,
half-length, bust, full-length), by **genre** (interiors, groups, architecture
and travel, reproductions, objects), and by **physical artifacts of the
archive** (film edges and perforations, mounts). Portraits dominate: the seven
portrait-led clusters contain 55.1% of the images. Cluster boundaries overlap
(silhouette 0.059), so the clusters are best read as neighborhoods on a
continuum rather than discrete categories. The results support the claim that
computational tools make collection-scale structure visible, while showing that
generic models encode the archive's materiality as strongly as its imagery.

## 1. Introduction

Man Ray's photographic estate at the Centre Pompidou is dominated by negatives
and prints of portraits, alongside fashion, documentation of artworks,
architecture, and experimental work. At around twelve thousand items, the
collection is typical of photographic holdings: too large to be held in mind,
yet catalogued at the level of single records. Questions about practice, such
as how a photographer framed sitters, what share of the work was commercial
portraiture, or how negatives relate to printed outcomes, are questions about
distributions, and are hard to answer one record at a time.

The aim of this work is demonstrative. It asks whether a general-purpose image
model, with no training on photographs of this kind, can produce:

1. one graphic that shows the entire collection and its main groupings, and
2. detail views showing what images are grouped together, so an audience can
   judge the groupings for itself.

The user initially suggested portraits, and male versus female sitters, as
groupings to test. Portraits proved to be the dominant structure. Gender
classification was **not** attempted; reasons are given in section 6.

## 2. Data and provenance

**Source.** A previous web scrape of the Centre Pompidou collection catalog,
stored at `E:\PM_laptop_backup\mydocs\MR_scrape\`. It comprises a catalog
table, `master.csv` (SHA-256 `bf313855...002b8e`), and an `images\` folder of
JPEG thumbnails. The catalog's medium-size web derivatives are about 500 px on
the long side (about 0.22 GiB in total). Source files were read but never
modified.

**Linking.** Each catalog image URL of the form
`.../picture/AA/BB/<hash>/thumb_medium.jpg` corresponds to the local file
`AA_BB_<hash>.jpg`.

| Item | Count |
|---|---:|
| Catalog records | 12,469 |
| Local JPEG files | 11,966 |
| Records linked to a local image (**analyzed set**) | **11,965** |
| Records with URL but no downloaded image | 446 |
| Records without an image URL | 58 |
| Local files matching no record (`blank.jpg`, gray placeholder) | 1 |
| Byte-identical duplicate image pairs (retained) | 3 |
| Unreadable images | 0 |

**Attribution.** In the analyzed set, 11,921 records are attributed to
Man Ray alone; 41 to Constantin Brancusi; 2 to "Anonyme (legs Brancusi)"; and
1 to Man Ray with André Breton. All 11,965 were embedded; a Man-Ray-only
overlay map (11,921 points) shows that the 44 other records do not change the
structure.

**Medium.** Catalog medium/technique text was normalized into three classes
for evaluation: **negative** 6,659 (55.7%), **print** 4,761 (39.8%), and
**other/unknown** 545 (4.6%). These classes were used only to evaluate and
color the maps, never as model input.

## 3. Methods

### 3.1 Pilot: should negatives be inverted?

Negatives and positives of the same subject are tonal opposites, so a model
might group images by polarity instead of content. Before scaling up, a pilot
on a stratified random sample of 384 images (156 negatives, 128 prints,
100 other; seed 20261017) compared two representations: originals, and the
same images with catalog-identified negatives inverted. Both used the pipeline
of sections 3.2-3.4.

| Pilot measure | Originals | Inverted negatives |
|---|---:|---:|
| Same-medium rate among 10 nearest neighbors (random baseline 34.2%) | 53.8% | 58.7% |
| Cluster/medium NMI | 0.141 | 0.147 |
| Silhouette (PCA space) | 0.091 | 0.090 |

On average, 60% of each image's ten nearest neighbors were the same in both
representations. Inversion changed neighborhoods but did not reduce medium
dependence; medium association was marginally higher. Polarity is therefore
not the main reason the model separates negatives from prints. Other
material cues, such as film borders, edge numbering, density, mounts, and
paper tone, also contribute. All later work used **original, uninverted**
images, which also avoids relying on catalog medium labels as an input.

### 3.2 Image preprocessing and feature extraction

Each image was EXIF-orientation-corrected, converted to RGB, and letterboxed
(full frame, no cropping) into a 224 x 224 square padded with neutral gray
(128) before standard ImageNet normalization. Features were taken from
**torchvision ResNet18** with `IMAGENET1K_V1` weights (SHA-256
`f37072fd...0e07ec`). This is a convolutional network trained to classify
ImageNet photographs into 1,000 object categories. The 512-dimensional
global-average-pooled activations before the classification layer were used
as the image descriptor and L2-normalized. Inference ran on CPU with four
threads. The model received no fine-tuning or Man Ray data, so any structure
reflects generic visual similarity.

### 3.3 Dimensionality reduction and clustering

- **PCA.** Fitted to all 11,965 feature vectors, keeping 32 components
  (randomized solver, seed 20261017). PC1 explains 9.41% of variance, PC2
  4.89%, the first two together 14.30%, and all 32 together 56.09%.
- **k-means.** Run on the 32 PCA scores with k = 16 and 20 initializations.
  k was chosen for legibility: enough groups to separate visible genres, few
  enough for a readable legend. It was not optimized, and no stability study
  has been made (section 7).
- **Internal and external measures.** The silhouette coefficient on a
  2,000-image random sample was 0.059. Normalized mutual information (NMI)
  between clusters and the three medium classes was 0.194.

### 3.4 Two-dimensional map

t-SNE (scikit-learn 1.6.1) was applied to the 32 PCA scores, with perplexity 40,
1,000 iterations, PCA initialization, automatic learning rate, and seed
20261017. t-SNE preserves **local** neighborhoods; distances between distant
regions, and region sizes, are not meaningful. PCA maps (PC1 vs. PC2) were
produced as a linear, globally faithful but less separated comparison.

### 3.5 Visualizations

All graphics use a neutral dark-gray RGB (38, 38, 38) background for projection
and Acrobat display.

- **Scatter maps** of the t-SNE and PCA spaces, colored by cluster, medium,
  catalog date, title cues, and attribution.
- **Grid atlas.** Every image assigned to one cell of a 110 x 109 grid by
  recursive balanced spatial cuts of the t-SNE coordinates (120 px cells;
  13,200 x 13,080 px). This removes overlap but displaces images, so it is not
  distance-preserving.
- **Exact t-SNE atlas.** Every thumbnail drawn at its exact t-SNE coordinate,
  using a single uniform scale with the y-axis flipped, so the layout matches
  the scatter maps. Overlap is resolved by a seeded random draw order (seed
  20261017) rather than any cluster order, so no cluster systematically covers
  another. The labeled page is 2400 x 1500 pt with thumbnails at most 15 pt;
  text-free 16:9 pages are 2400 x 1350 pt with a 12 pt margin (about 15.7 pt
  thumbnails). PNG exports are 9600 x 6000 and 9600 x 5400 px. Optional thin
  outlines in the cluster color reveal membership without moving images.
  Thumbnails were composited in 250-image batches, because placing about
  12,000 images directly on one PDF page is prohibitively slow.
- **Detail sheets.** For each cluster, 12 images: 6 nearest the centroid,
  3 seeded random members, and 3 edge members (furthest from the centroid).
  This shows typical, arbitrary, and borderline content: 192 images in all.
- **Final five-page atlas.** (1) no outlines; (2) outlines for display
  clusters 0-9 only (8,541 images, mainly portraits and people); (3) labeled
  page with legend (n and %); (4) all outlines; (5) a single outlined locator
  image, *Le Violon d'Ingres*. Image objects are reused across pages, so
  placement and pixels are identical on every page.

### 3.6 Semantic labeling protocol

The clusters were named after inspection, not by the model. For each cluster,
the 12-image detail sheet was examined alongside catalog titles and medium
counts, and a short descriptive label plus an evidence note was recorded in
[cluster_labels.json](../cluster_labels.json). Labels describe what dominates
visually (framing, genre, material); they claim no sitter identity, gender,
date, or intent. The labels are bound to a hash of the reviewed coordinates;
if the analysis is re-run and clusters change, the software withholds the
labels and issues a warning. For presentation, the user reordered the
clusters into a "portrait-first" display sequence. This reordering changes
only the numbers and legend order, not cluster membership or colors.

### 3.7 Verification

Unit tests cover grid assignment, the coordinate transform, and the
display-order mapping. Validator scripts check every export: image counts,
the number of embedded thumbnails per atlas page (11,965), placement against
the recorded coordinates (tolerance 0.003 pt), outline counts (0 / 8,541 /
11,965 / 1), legend counts and percentages, page sizes, and source-file
hashes. Successive editions were confirmed pixel-identical on shared pages.

## 4. Results

### 4.1 Cluster composition

Display order (portrait-first) with original k-means IDs, provisional labels,
sizes, and dominant catalog medium.

| Display | Original | Label | n | % | Dominant medium |
|---:|---:|---|---:|---:|---|
| 0 | 0 | Seated portraits / marked prints | 749 | 6.3 | print 97% |
| 1 | 4 | Seated portraits / negatives | 922 | 7.7 | negative 98% |
| 2 | 5 | Half-length portraits / prints | 976 | 8.2 | print 93% |
| 3 | 15 | Bust portraits / gestures / prints | 748 | 6.3 | print 87% |
| 4 | 6 | Front-facing portraits / negatives | 1,226 | 10.2 | negative 95% |
| 5 | 1 | Dark-toned portrait prints | 764 | 6.4 | print 81% |
| 6 | 12 | Portraits / poses / negatives | 1,211 | 10.1 | negative 97% |
| 7 | 14 | Full-length / fashion / costume | 507 | 4.2 | negative 58% |
| 8 | 8 | Interiors / people in settings | 646 | 5.4 | negative 80% |
| 9 | 9 | Groups / horizontal scenes | 792 | 6.6 | print 58% |
| 10 | 10 | Reproductions / framed forms | 739 | 6.2 | negative 85% |
| 11 | 11 | Architecture / landscapes / travel | 746 | 6.2 | print 51% |
| 12 | 2 | Mounted images / graphic material | 358 | 3.0 | negative 42% |
| 13 | 13 | Body studies / expressive poses | 588 | 4.9 | negative 54% |
| 14 | 7 | Objects / masks / graphic forms | 721 | 6.0 | negative 64% |
| 15 | 3 | Film edges / perforations | 272 | 2.3 | negative 62% |

Percentages use n = 11,965 and may not sum to 100 because of rounding.

### 4.2 Findings

1. **Portraiture dominates the collection.** Display clusters 0-6 are
   portrait-led and hold 6,596 images (55.1%). Adding full-length/fashion,
   interiors with people, groups, and body studies (clusters 7-9 and 13)
   brings people-centered images to roughly three-quarters. This quantifies
   what is often said qualitatively: the estate is, above all, a record of a
   portrait practice.
2. **Material state is a primary axis.** The model separates negatives from
   prints even for the same subject type. Seated portraits split into a print
   cluster (0, 97% prints) and a negative cluster (1, 98% negatives), and
   other portrait clusters show the same pattern. Six clusters are at least
   93% one medium. For a curator this is both a finding and a warning: the
   archive's physical stages (negative to print) are visible at scale, but
   generic features conflate *how an image exists* with *what it depicts*.
3. **Framing conventions are separable.** Within portraits, the space
   distinguishes seated, half-length, bust (often with hand gestures),
   front-facing, and full-length framings. This points toward studying a
   studio's repertoire of poses and croppings quantitatively.
4. **Archive artifacts form their own regions.** Film edges and perforations
   (cluster 15) and mounted or graphic material (cluster 12) gather
   separately. These are signatures of the archive's physical form and of
   catalog digitization practice, not of Man Ray's subjects.
5. **Non-portrait genres are distinct.** Reproductions and documentation of
   artworks (10), architecture, landscape, and travel (11), and objects and
   masks (14) occupy distinct regions. Reproductions are 85% negatives, which
   is consistent with documentary copy work.
6. **Boundaries are soft.** The low silhouette (0.059) and the mixed edge
   members on the detail sheets show that the collection is a continuum.
   Clusters are useful handles for navigation, not natural kinds.
7. **Case study: *Le Violon d'Ingres*** (1924, AM 1993-117, record 774). The
   model places the print in display cluster 14, "Objects / masks / graphic
   forms," rather than among portraits. The f-holes and the treatment of the
   body as an object seem to be read as graphic form. The model's
   "misreading" echoes the work's own conceit of body as instrument. This
   makes a useful talking point about what a model sees, and should not be
   presented as an interpretive result.

### 4.3 Pilot result

Inverting negatives did not reduce the dominance of medium in the embeddings
(NMI 0.141 vs. 0.147). Material separation is therefore not just tonal
polarity, and simple inversion is not a remedy (section 3.1).

## 5. Discussion

The exercise supports the presentation's central argument. A generic,
untrained model and standard statistical tools, run on a laptop CPU, can
place every image in a large photographic holding on one surface, where
neighborhoods are visually coherent and the main structures (portrait
dominance, framing repertoire, genre regions, negative/print duality) are
evident at a glance. The atlas also makes the method auditable: a viewer can
zoom into any region in Acrobat and see that it contains what the legend
claims, or that it does not.

The results also show the limits of generic features. An ImageNet classifier
was trained to recognize objects, not photographic practice. Its sensitivity to
tone, borders, and support is why material state organizes the space so
strongly. For the history of practice this is not purely a defect, since the
negative/print relationship is itself of interest, but it means that
content-based questions need models or preprocessing that factor material out.

## 6. Limitations and ethical considerations

- **Model choice.** ResNet18 with ImageNet weights is small and dated. Its
  features capture texture, tone, and layout more than semantics.
- **Arbitrary k and no stability analysis.** k = 16 was chosen for
  presentation. Clusters may change with seed or k; labels are provisional
  and were drafted from 12-image samples per cluster.
- **t-SNE distortion.** Only local neighborhoods are meaningful; global
  positions, gaps, and region areas should not be interpreted.
- **Input resolution.** Analysis used catalog web thumbnails (about 500 px),
  downsampled to 224 px. Fine detail, inscriptions, and retouching are not
  visible to the model.
- **Catalog dependence.** Medium classes come from normalized free-text
  catalog fields. 504 catalog records lack images, and a few non-Man Ray
  records (44) are included.
- **No identity or gender inference.** Classifying sitters as male or female
  from appearance was deliberately not done. Automated gender inference is
  unreliable, especially for 1920s-30s styling, costume, and the deliberate
  gender play in Man Ray's work (for example the Rrose Sélavy portraits of
  Marcel Duchamp). It also imposes a binary on historical people who cannot
  consent. A defensible version would use catalog sitter names linked to
  authority records, with human review.
- **Rights.** Images are Centre Pompidou catalog derivatives of works under
  copyright. Public display requires appropriate credit and clearance.
- **Not reviewed in Acrobat.** The final PDFs were verified programmatically
  but have not had a manual viewing review.

## 7. Fruitful next steps

Ordered roughly from cheapest to most ambitious.

1. **Cluster stability.** Re-run k-means across seeds and k = 8-24, measuring
   adjusted Rand index between runs and a consensus clustering. Report which
   groupings are robust. Compare t-SNE with UMAP and with several t-SNE seeds.
2. **Better encoders.** Replace ResNet18 with self-supervised or
   vision-language models such as DINOv2 or CLIP/SigLIP. These tend to
   capture composition and semantics better. CLIP also enables text queries
   ("seated woman with hat," "rayograph," "solarization") over the collection.
3. **Factoring out material.** Automatically crop film borders and mounts,
   normalize tone, and train or select features that are invariant to
   negative versus print, using negative/print pairs as supervision. Then
   re-ask the content questions.
4. **Negative-to-print matching.** Use near-duplicate retrieval on inverted
   negatives and prints to link each print to its source negative. Measure
   which negatives were printed, how they were cropped, and how often.
   This bears directly on selection and editing practice, and is the most
   promising route to a substantive art-historical finding.
5. **Sittings and sequences.** Cluster very near neighbors to reconstruct
   portrait sessions (consecutive frames of one sitter). Study how many
   exposures a sitting produced and how poses varied.
6. **Linking to catalog metadata.** Parse dates, sitter names, and inventory
   series, then map them onto the space. This shows how framing, genre, and
   material change over time, and supports a name-based (not
   appearance-based) analysis of sitters, including gender, if wanted.
7. **Human-validated labels.** Have a specialist label a stratified sample.
   Measure cluster purity and turn provisional labels into a documented
   coding scheme with agreement statistics.
8. **Higher-resolution sources and comparison collections.** Request
   higher-resolution files from the Pompidou. Add other holdings (for example
   the existing Met and rayograph scrapes in `projects\man_ray`) to compare
   collections within one space.
9. **Interactive atlas.** Publish a zoomable web viewer (deep-zoom tiles with
   catalog links) as a companion to the static PDFs.

## Appendix A. Reproducibility

| Item | Value |
|---|---|
| Seed (sampling, PCA, k-means, t-SNE, draw order) | 20261017 |
| Python / platform | 3.13.2, Windows, CPU (4 threads, `LOKY_MAX_CPU_COUNT=4`) |
| Packages | numpy 2.2.4, pandas 2.2.3, Pillow 11.1.0, scikit-learn 1.6.1, matplotlib 3.10.3, PyMuPDF 1.27.2.2, torch 2.14.1+cpu, torchvision 0.29.1+cpu |
| Model weights | ResNet18 `IMAGENET1K_V1`, SHA-256 `f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec` |
| Catalog | `master.csv`, SHA-256 `bf31385581186c7bc40b0d47db83b443f35f09bc69d15a1681c58074ec002b8e` |
| Coordinates | `coordinates.csv`, SHA-256 prefix `a8e4bddb`, identical in all editions |
| Code | [full_space.py](../full_space.py), [tsne_atlas.py](../tsne_atlas.py), [highlight_atlas.py](../highlight_atlas.py), [pilot.py](../pilot.py) |
| Run record | `outputs\full_space\summary.json` (versions, hashes, parameters, metrics) |

Commands for rerunning are in [RESTART_HERE.md](../RESTART_HERE.md). CPU
floating-point and library-version differences can change k-means or t-SNE
results slightly. A full rerun should be compared, not assumed identical, and
labels must be reviewed again if cluster membership changes.

## Appendix B. Output inventory (latest editions)

- `outputs\full_space_highlight\space_tsne_image_atlas.pdf`: five-page
  atlas (section 3.5), plus a 9600 x 5400 PNG of the highlight page and
  `highlight_summary.json`.
- `outputs\full_space_four_page\`: presentation PDF, t-SNE and PCA maps with
  overlays (`space_*.png`), legend with n and % (`cluster_semantic_legend.*`),
  16 detail sheets (`neighborhood_00.png` to `neighborhood_15.png`, chosen in
  `detail_selections.csv`), grid atlas (`space_image_atlas.*`),
  `coordinates.csv` (per-image catalog fields, PCA and t-SNE coordinates,
  original cluster ID), `display_coordinates.csv` (display cluster IDs),
  `tsne_atlas_placements.csv`, `embeddings.npz`, `pca_scores.npy`, and
  `summary.json`.
