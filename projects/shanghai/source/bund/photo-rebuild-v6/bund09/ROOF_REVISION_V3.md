# Bund09 roof-continuity-v3

The actual v2 native preview, viewed against the current P01 photograph, showed smooth uncovered triangles and strips at the southern short-wing and rounded-return roof joins. P01 shows tiles continuing across those visible slopes. The v2 model, native, preview and failed overall appearance review are preserved in the sibling `bund09-visible-detail-v2` stage; its raw SHA is `7e38b487a82f626e9a43ef7bbf0ba8b33903798dec63c06de7f4bb319b962815`.

V3 changes only the two gray roof-tile material meshes. It retains the original source polygon, the estimated 1.95 m roof inset and 1.40 m rise. Every tile vertex uses the same continuous modeled roof-height function based on distance to the original polygon boundary. The new method clips each tile against its roof-direction domain and retains valid edge pieces instead of rejecting an entire tile when one corner crosses a slope boundary. The short source facets 12–14 and joins 10/16 now receive continuous tile coverage. No flat box is inserted over the gaps.

Nineteen boundary-site Voronoi domains partition the modeled skirt. These domains assign tile direction; they are **not** measured historic hip lines. Edges 9–18 carry the photographed/front-facing tiled field. Rear domains 0–8 remain explicitly inferred roof support, and the large inset roof cap is byte-for-byte unchanged. The source map polygon's rounded corner is faceted; the reconstructed tile field follows that frozen geometry and does not claim a surveyed curved roof.

Each finite-thickness tile has one closed corrugated section combining a rounded cover ridge and a shallow pan valley. This avoids independent cover/pan solids penetrating each other at course overlaps. The section thickness is an estimated 9 mm, with 220 mm column pitch, 260 mm horizontal course pitch, 320 mm tile length and 20 mm lap lift. The one photographed southern cap-tile line retains an estimated corner-bisector path, with a raised finite-thickness section. Exact tile profile, dimensions, joints and hip path remain proportional estimates.

The geometry report checks complete plan coverage of the ten tiled domains, disjoint roof-direction domains, adaptive surface interpolation error and positive course clearance after allowing for surface approximation. Tile refinement propagates shared edge splits so it remains conforming; it does not subdivide the entire roof uniformly. The supporting roof sheets follow the same height function, 25 mm below the tile datum. The cap-to-tile-envelope check is explicitly sampled and does not claim a complete Boolean intersection proof. Actual FLOAT32 per-part closure, winding, nondegenerate triangles and positive volume are checked separately.

`check_roof_revision.py` compares actual v2 and v3 GLBs: all ten non-roof material batches must keep exactly equal index and attribute arrays. This includes all glass positions and UVs, original embedded JPEG bytes, brick, stone radial arch partitions, balcony corner posts, every baluster, frames, gold lettering and the inferred zinc roof cap. Original opening records, dimensions, source footprint and model bounds are also required to match.

The central balcony retains nine front balusters as an estimate. The oblique current P01 crop resolves about eight visible shafts; this view alone does not establish the total behind the near post. V3 therefore does not change that count without firmer current evidence.

These numerical checks are separate from visual acceptance. The actual new native render, root independent reopen and targeted native/photo comparison are recorded separately in `native-compressed/appearance-review.json`, `reopen-check.json` and `rear-roof-range-check.json`. Southern continuity passed the targeted visual check; the rear support facets remain unobserved estimates. V2's preview used 12° elevation, while the earlier `glass-inset-v1` preview used 8°; those images are not a same-camera A/B test. Dark windows behind the open loggias remain consistent with shaded regions of P01 and are not globally brightened.

Reproduce with ordinary Python and the unchanged sibling `../common`:

```sh
python build_model.py --output output
python check_photo_uv.py --output output
python check_roof_revision.py --before /retained/bund09-visible-detail-v2/output/bund09-raw.glb --after output/bund09-raw.glb
```

Source rights remain unchanged: original geometry/code MIT, OSM/Overture provenance retained, Suicasmo P01 CC0, dated Legolas1024 P02/P03 CC BY-SA 4.0 and the sign font SIL OFL 1.1. Shared helpers and the main project are not modified.
