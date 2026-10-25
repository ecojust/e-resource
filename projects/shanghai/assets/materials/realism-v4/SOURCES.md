# Surface textures for the Bund viewer

These nine 1024 × 1024 JPEG maps are unmodified Poly Haven downloads, totalling
4,898,227 bytes (4.67 MiB). The largest file is 1,056,664 bytes. Base colour is
sRGB; roughness and OpenGL normals are linear data. No facade photographs,
window images, baked building shadows or aerial imagery are included.

| Asset | Author | Source | Maps |
| --- | --- | --- | --- |
| Sandstone Blocks 08 | Rob Tuytel | https://polyhaven.com/a/sandstone_blocks_08 | Base colour, OpenGL normal, roughness; 1K JPG |
| Granite Tile 03 | Charlotte Baglioni | https://polyhaven.com/a/granite_tile_03 | Base colour, OpenGL normal, roughness; 1K JPG |
| Clean Asphalt | Dimitrios Savva | https://polyhaven.com/a/clean_asphalt | Base colour, OpenGL normal, roughness; 1K JPG |

All three assets are **CC0-1.0**. Author names come from the provider's asset
metadata, retrieved on 2026-10-25. Provider licensing statement:
https://polyhaven.com/license . It explicitly permits redistribution, including
assets shared within another work. License summary and legal terms:
https://creativecommons.org/publicdomain/zero/1.0/ .

`manifest.json` records the exact original file URLs, provider MD5 hashes,
download sizes, independently calculated SHA-256 hashes, image dimensions,
authors, source descriptions, and the sampling regions used by the viewer.
The original assets can be downloaded or verified independently.

## What the viewer uses

The photographs represented in these generic material maps were not taken from
the Shanghai buildings in this scene. They supply close-up surface grain; they
do not establish the actual quarry, stone species, historical finish or present
weathering of any particular building. Sandstone is used as a restrained grain
analogue on existing pale-stone materials, not as a claim that those buildings
are made of that sandstone. The original building colours remain in control.

To avoid false masonry courses, the shader samples only seam-free stone interiors
and mirrors those regions. It does not alter the source images:

- Sandstone: pixels x=360..619, y=225..379, with top-left image origin. The source
  covers 3 × 3 metres; this sampled patch represents about 0.762 × 0.454 metres.
- Granite: pixels x=24..315, y=24..485. The source covers 1.802 × 1.802 metres;
  the sampled patch represents about 0.514 × 0.813 metres.
- Asphalt: full image, 2.1 × 2.1 metres. The provider dimensions are converted
  from millimetres and are not a site survey.

Colour variation, roughness and normal strength are deliberately reduced. Stone
grain and normals fade as their footprint gets small on screen. Geometry remains
responsible for facade courses, openings, columns, moldings and reliefs. Paving
alone gets an estimated 0.80 × 0.42 metre running-bond layout with 6 mm joints,
faded with screen coverage. Those paving dimensions are a scene approximation,
not measured Shanghai data.

The implementation uses transformed world positions, including meshopt decode
node scale, instancing and batching. It requires no mesh UVs and adds no global
environment reflections. Source textures are shared across buildings and LODs.
