# Independent photo proportion calibration: Bund 05, 06 and 14

The original 2025 Suicasmo photographs were inspected and their EXIF checked. For Bund 05 and 14, stored JPEG pixels are **5184 × 3456, Orientation 6**; the display-oriented image is **3456 × 5184**. These files report Canon EOS M2, 24 mm for Bund 05 and 21 mm for Bund 14. Bund 06 instead uses Orientation 1 and 22 mm, as detailed below. Original image bytes were not changed. Analysis figures include only derivative calibration views, not replacement textures.

Canon's own [EOS M2 Camera Museum specification](https://global.canon/en/c-museum/product/dslr817.html) states **“Image sensor size Approx. 22.3 x 14.9 mm.”** The official URL, short specification quote and retrieved-source SHA-256 are recorded in `camera-source/canon-source.json`; `fetch-log.json` records retrieval attempts. Numerical reproduction does not depend on redistributing the full Canon page or text. This is an approximate intrinsic prior, not a lens calibration. The EXIF focal-plane-resolution fields imply approximately 22.71 × 15.16 mm, about 1.8% larger; sensitivity runs include 2% focal-scale standard deviation, principal-point uncertainty, point-picking uncertainty and ±0.3 m standard deviation for the mapped width/corner correspondence. Lens distortion and undocumented image processing remain uncalibrated.

`photo_metric.py` fits two orthogonal directions in camera-ray space to the selected parallel horizontal and vertical line families. It intersects normalized image rays with a single nominated front plane, then fixes scale with the frozen OSM main front segment: **20.1426 m for 05, 23.1745 m for 14**. Main front corner lines are extrapolated to the nominated ground line where pedestrians, planters or the image crop obscure their feet. Thus the baseline also has uncertainty. This avoids using raw low-angle pixel height/width ratios.

Each building directory contains:

- `calibration-independent-controls.json`: original oriented-pixel controls, their interpretations and uncertainty assumptions.
- `calibration-independent.json`: intrinsics, fitted vanishing points, normalized rays, camera pose in facade coordinates, full pixel/metric matrices, per-point heights and 256-sample sensitivity results.
- `calibration-independent-comparison.png`: selected controls on the original view beside a metric rectification of the nominated plane. Side returns, projecting bays and roof offsets in the illustrative warp are explicitly **not** corrected.

| Building | Photo-plane estimate | Interpretation |
|---|---:|---|
| 05 main deep cornice front band | 23.8 m | With 0–0.6 m outward depth, nominal height becomes 23.5–23.8 m. Approximately 23–25 m is an appropriate modeling allowance. |
| 05 triangular pediment tips | 28.76 / 29.02 m | Two independent same-feature picks agree within 0.26 m; the triangle rise is about 1.5–1.7 m, not 2.3 m. |
| 05 higher stone fins | 29.12 / 29.49 m projected to front plane | They have uncertain depth and are not identical to the triangular tips. Approximately 28.5–31.5 m allows for picking and a modest setback. Flagpoles are excluded. |
| 05 middle balustrade cap | 28.0 m | Its depth is uncertain; treat as a proportion estimate. |
| 14 flat wing coping | 24.62 / 24.55 m | About 23.5–26.5 m after practical uncertainty; not the protruding end fins or central tower. |
| 14 highest central stone spine | 33.4 m projected to front plane | Conditional on ±1 m outward/setback depth, nominal height is 32.47–34.34 m; the broader propagated envelope is approximately 30.9–35.9 m. A farther rear setback requires a new depth assumption. |

These ranges are **not measured heights or statistical survey confidence intervals**. They do not independently establish unseen rear heights. The data do not support treating the initial 14 model's 28.8 m flat coping and 38.2 m stone spine as calibrated measurements. The 05 draft's 23.6 m cornice was already consistent; its steep triangular gables and oversized attic windows needed proportion review instead.

The visible 05 small central attic window mouths are approximately 1.3–1.4 m wide and 1.4–1.5 m high, bottom near 24.2–24.3 m; the broader arched attic window mouths are about 3.5 m wide, 1.8–2.0 m high, with roughly 0.75 m rise. Main central fourth-level mouths are approximately 1.4–1.5 × 2.3 m. These refer to dark frame/opening boundaries, not the outer stone surround. Absolute horizontal placement in 05 remains uncertain by roughly 0.4 m because the mapped corner has small changes of plane; relative bay spacing is more reliable.

## Projection contract

Use homogeneous column vectors. `oriented_pixel_to_facade_u_z` maps `[pixelX,pixelY,1]` to `[u,z,1]` after division by the third coordinate. Its inverse is `facade_u_z_to_oriented_pixel`. `facade_u_z_d_to_oriented_pixel_projection_3x4` maps `[u,z,d,1]` to image coordinates, where **positive d points outward toward the camera** and negative d is recessed/backset. `u` is left-to-right in these front-facing photos, corresponding to the frozen CCW front-edge tangent; `z` is up. The facade origin is the midpoint of the extrapolated two base corners, not the image center.

Orientation 6 uses pixel-center coordinates:

```text
oriented_x = 3455 - stored_y
oriented_y = stored_x
stored_x   = oriented_y
stored_y   = 3455 - oriented_x
```

Both direction matrices and `stored_pixel_to_facade_u_z` are included. These are pixel coordinates, not an implicit choice of glTF UV vertical convention. Preserve the original image bytes and the existing runtime EXIF handling; derive UVs using the exporter's explicit pixel-to-UV convention.

The homographies are **initialization and comparison tools**, not ready-made whole-wall texture maps. Before sampling a recessed glass plane, use its own depth and register the actual aperture corners; projecting bays, side facades and roofs cannot share a single common-plane mapping. Street lamps, people, signs, foliage and occluded panes must be excluded. No modeler script or production asset was changed by this calibration.

Reproduction:

```sh
python common/photo_metric.py bund05/calibration-independent-controls.json --samples 256
python common/photo_metric.py bund14/calibration-independent-controls.json --samples 256
python common/test_photo_metric.py
```

The synthetic known-camera fixture recovers the metric plane and camera position, verifies all four Orientation-6 corner mappings and the Orientation-1 identity mapping, and checks nonzero facade depths through the 3×4 projection matrix. It validates the mathematics, not the real-world accuracy of the manually selected photographic controls. Photos: Suicasmo, CC0-1.0; map footprint source: © OpenStreetMap contributors / Overture Maps Foundation, ODbL-1.0.

## Bund 06 extension

The contemporary [China Merchants Bank photograph](https://commons.wikimedia.org/wiki/File:China_Merchants_Bank_Building,_Shanghai_20250501.jpg) is also Canon EOS M2, but has **22 mm focal length and Orientation 1**. Its stored and displayed size are both **5184 × 3456**. Do not apply the portrait Orientation-6 matrix to it. The same ray/orthogonality method uses only the **32.2183 m main front plane**. The separate 6.1187 m annex and connecting setback are excluded from the width calibration. Manual controls use a 1920 × 1280 inspection view and are scaled by 2.7 to source pixels. The main left boundary is the wall corner below the annex return, not a window jamb or the annex outer corner.

The fit has approximately 3.99 source-pixel endpoint RMS (1.48 inspection pixels), with a plausible inferred camera height of 1.93 m and perpendicular facade distance 39.03 m. Independent estimates are:

| Feature | Nominal plane height |
|---|---:|
| Main cornice | 13.95 m; practical allowance roughly 13.2–14.6 m |
| Main horizontal story bands | approximately 4.8 / 9.45 / 13.95 m |
| Central triangular stone apex | 22.03 m |
| Highest central stone finial | 22.99 m; practical allowance roughly 21.8–24.2 m |
| Small gable apex examples | 18.45 / 18.64 m |
| Outer round-pinnacle finials | approximately 18.0 m |
| Inner round-pinnacle finials | approximately 19.25 m |

Selected third-story window mouths have bottom near 10.4 m and height near 2.45 m; second-story mouths bottom near 6.0 m and height near 2.1 m. The central attic mouth is near 14.94 m + 2.53 m, and a small attic mouth near 14.65 m + 1.50 m. These support more substantial solid panels below the openings than the initial model; they do not imply adding extra principal floors. Window quadrilaterals are rough bounds, especially at arches, and need separate corner registration before texture use.

The existing proposed ridge **21.25 m high at 6.9 m behind the front** is a separate depth hypothesis. The calibrated projection maps examples at `u=-12,+8 m` to roughly `(618,298)` and `(1371,260)` in the 1920-pixel inspection view, close to the visible rear-roof ridge band. This is a consistency check, not an independently measured ridge. It explains why assigning that roof's lower image Y directly to the front-plane homography would incorrectly lower it. No annex or rear facade dimensions were recalibrated here.

`photo_metric_portrait_v1.py` preserves the exact earlier 05/14 tool snapshot matching their recorded source hash. The current `photo_metric.py` only generalizes orientation/dimension labels and figure sizing for the landscape 06 image; numerical fitting equations are unchanged. Run 06 with `python common/photo_metric.py bund06/calibration-independent-controls.json --samples 256`.
