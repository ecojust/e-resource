# Independent single-photo proportion checks: Bund 07 and 09

The 2025 Suicasmo original photographs were inspected, including enlarged stone courses and window mouths. Both are unmodified Canon EOS M2 JPEGs, **5184 × 3456, EXIF Orientation 1**; focal lengths are 25 mm for 07 and 31 mm for 09. Source bytes, licenses and SHA-256 are retained in each calibration record. The original Canon [EOS M2 specification](https://global.canon/en/c-museum/product/dslr817.html) states “Image sensor size Approx. 22.3 x 14.9 mm.” The existing camera-source JSON retains that short quotation and retrieval provenance; numerical reproduction does not require redistributing Canon's full page.

The already frozen `../../common/photo_metric.py` is reused unchanged, SHA-256 `dcab74584b59a7c891bbf13125b9c693908bb8ffcdac50444489d834abc8019c`. No 05/06/14 calibration or shared tool was edited. It fits orthogonal horizontal/vertical line directions in normalized camera rays, fixes scale with the exact mapped front-edge width and derives a single-plane homography plus a full facade-depth projection. This is a photographic proportion check, **not a survey, laser scan or calibrated photogrammetric reconstruction**.

Manual controls were chosen in 1920 × 1280 inspection coordinates and scaled by 2.7 to source pixels. Continuous stone-line corridors were refined against image gradients. All final endpoints and their meanings are explicit in the controls; the refinement audit retains rejected candidates. In 07 the apparent left wall boundary crosses projecting pilasters at different depths, so it was rejected as a pose-direction line. Width-corner correspondence remains a separate uncertain assumption. No camera height, symmetric roof height or pre-existing model height was imposed on the fit.

## Results

| Feature | 07 | 09 |
|---|---:|---:|
| Frozen main front width | 29.329667 m, original edge 3 | 21.554476 m, original edge 17 |
| Control endpoint RMS | 3.252 source pixels | 3.465 source pixels |
| Inferred camera height / perpendicular distance | 1.19 / 34.82 m | 1.09 / 38.04 m |
| Main roof cornice | Lower edge 18.96 m; parapet top 19.94 m | Top 14.29 m; lowest architrave edge 12.82 m |
| Front stone pediment tips | 21.55 / 21.51 m | 16.18 / 15.91 m |
| Main story bands above ground datum | 4.84 / 9.36 / 14.18 m | 4.43 / 9.27 m |

These nominal values guide model proportions. The 256-sample sensitivity runs vary line endpoints, uncertain mapped corners and ground, focal scale, principal point and mapped width. The broader stated envelopes are approximately **17.1–20.6 m** for 07's main cornice, **19.4–23.4 m** for its stone pediments, **12.9–15.7 m** for 09's cornice and **14.5–17.8 m** for its stone pediments. They are not survey confidence intervals and do not cover unknown lens distortion or unrecognized plane offsets. Thresholds obscured by plants, a strong oblique view and approximate intrinsics limit absolute heights. Small residual differences between matching left/right features must not be manufactured as deliberate architectural asymmetry.

The 2016 near-front 07 photo was inspected as an independent visual cross-check of four principal stories and their proportions. It was not used as an additional calibrated camera, and no Nikon camera specification was assumed in this calculation. The OSM seven-floor attribute remains an unverified map attribute, not an instruction to add three floors to the visible facade.

## 07 openings and axes

Enlarged original-image controls measure the outer dark aperture mouth, including the head reveal, rather than only the bright glass. A near central bay gives:

| Selected aperture | Bottom | Height | Width |
|---|---:|---:|---:|
| Second story | 6.067 m | 2.348 m | 1.102 m |
| Third story | 11.057 m | 2.048 m | 1.248 m |
| Fourth story | 16.184 m | 1.955 m | 1.284 m |
| Near left wing, fourth-story wide opening | 16.293 m | 1.966 m | 1.465 m |

These reject a uniform 2.75 m opening height for those selected bays. They do not establish the dimensions of every doorway, side facade or narrow wing window. The far wing's visible width is partly occluded by columns, so it is not treated as a complete opening-width measurement. The `calibration-axis-check.json` records eleven visible fourth-story dark-window centers in the observed **3+5+3** grouping. The near wing center is around `u=-10.4 m`, the far wing around `u=+10.2 m`; the five middle-axis estimates are about `[-5.63,-2.85,0.01,2.48,5.05] m`. Projecting wings, recessed windows and corner uncertainty introduce roughly 0.3–0.6 m practical horizontal ambiguity. The record therefore supports a coherent symmetric architectural layout rather than imposing every photographic parallax residual on the model.

The metal roof crowns project to about 22.5 m on the front plane. They are physically set back: assuming `d=-3..0 m` gives nominal crown heights roughly 22.4–24.4 m before the broader sensitivity envelope. Their urns and flagpoles are separate. The later blue rear extension is not part of this same front plane and has no independent height/depth solution here.

## 09 entablature and gallery

Additional controls at inspection x=1250 identify the cornice top, dentil underside, decorative frieze and lower architrave separately:

- Cornice top: 14.289 m.
- Dentil underside: 13.938 m.
- Frieze top/bottom: 13.699 / 13.258 m.
- Lowest architrave edge: 12.819 m.
- Adjacent capital top/bottom: 12.850 / 12.391 m.

This supports a thick entablature above the columns. The six approximate gallery-boundary centers in `calibration-axis-check.json` describe five spans; they do **not** enumerate every shaft in a double-column group. The separately observed shafts, end brick piers and attached columns must remain distinct in the model.

The outer gallery plane is calibrated; the recessed red-brick back wall is not the same plane. In the selected view, shadow, beam thickness and offsets prevent a defensible same-height, same-axis front/back tie point. Gallery depth is therefore **not independently determined**. A model's 1.85 m gallery depth remains an explicit architectural estimate, not an output of this calibration. Rear-window placement or photographic samples require that depth through the 3×4 matrix or separate individual registration. The south angled corner, short wing and rear roof platform likewise require separate plane/depth reasoning. The rear coping example is kept in the separate depth-check record and excluded from the rectified front-height plot.

## Projection and reproduction

For both images stored and oriented pixel-center coordinates are identical. The report includes both matrices explicitly; no Orientation-6 rotation should be applied. Use homogeneous column vectors:

- `oriented_pixel_to_facade_u_z`: `[pixelX,pixelY,1] → [u,z,1]`, divided by the third component.
- `facade_u_z_to_oriented_pixel`: inverse front-plane mapping.
- `facade_u_z_d_to_oriented_pixel_projection_3x4`: `[u,z,d,1] → image`, with **positive d outward toward the camera** and negative d behind the facade.

The origin is the midpoint of extrapolated mapped front-edge base corners; `u` follows the frozen front-edge tangent, `z` is up. The three-dimensional matrix is required for actual recessed glass. These data do not authorize a whole-photo wall plane or projecting trees, lamps, signs, people, columns or adjacent facades into windows.

From the `building-by-building-v6` staging root:

```sh
python common/photo_metric.py next/bund07/calibration-independent-controls.json --samples 256
python common/photo_metric.py next/bund09/calibration-independent-controls.json --samples 256
```

Final deliverables per building are `calibration-independent-controls.json`, `calibration-independent.json`, `calibration-independent-comparison.png`, `calibration-axis-check.json` and `calibration-depth-check.json`. The next/common summary contains final SHA/size records and verification of unchanged earlier reports/tools. Inspection crops and gradient candidates are analysis evidence only, not publication textures.

Photographs: Suicasmo, CC0-1.0. Map footprint: © OpenStreetMap contributors / Overture Maps Foundation, ODbL-1.0. Camera specification: Canon official source as linked above.
