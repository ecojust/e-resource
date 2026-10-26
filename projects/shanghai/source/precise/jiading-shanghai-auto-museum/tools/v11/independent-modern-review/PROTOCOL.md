# Independent modern-building geometry review

This directory contains a raw-GLB reader and finite geometric question engine.
It does not generate a model, import author construction routines, approve its
appearance, or certify physical structural safety. Author dimensions and role
records locate questions; only actual serialized triangles answer them.

## Prerequisites and identity

1. `audit_raw_structure.py --raw PATH --id ID --source-freeze PATH --output NEW`
   reads the actual uncompressed Float32 GLB, checks its SHA against the geometry
   sidecar, verifies every frozen author source file, and checks explicit part
   ranges against material primitive indices. Results use
   `modern-actual-raw-structure-v1` / `structure_passed`.
2. `modern-finite-requests-v1` is executable only when its state is
   `READY_FOR_ACTUAL_AUDIT`, checks are nonempty and `source_binding` names the
   exact raw, passing independent structure report, source freeze, source
   geometry and calibration SHA256 values. A missing selector cannot pass.
3. `run_finite_checks.py --raw PATH --requests PATH
   --source-structure-report PATH --output NEW` returns
   `modern-actual-finite-checks-v1` / `finite_checks_passed` with nonempty actual
   `check_results`. Each `id` is unique. The CLI adds `requests_file` and
   `checker_files`; the actual source structure file is separately SHA bound.
   Outputs are new immutable paths beneath this directory. Failed outputs stay.

`Asset` and `Part` are dataclasses in `modern_mesh.py`. Delivery adapters may
construct them from actual GLTFLoader-decoded world ENU arrays and call:

```python
run_checks(asset, requests, source_structure_report_path=path)
```

Part keys are exact compact JSON `[label,material,ordinal]`, preserving separate
solids with repeated labels. The adapter records actual delivery identity under
`asset.identity.asset`, decoded-array provenance and the semantic-source asset.
Raw identity is `asset.identity.raw`. Actual oriented positions are cyclically
normalized per triangle and sorted preserving multiplicity, then SHA hashed.
No coordinate is rounded, welded or repaired; signed zero is normalized only.
Every present delivery part must exactly match the independent raw position
proof. Missing raw keys must be explicitly listed in
`allowed_omitted_part_keys`; this does not itself authorize a particular LOD
deletion, which packaging must separately constrain to approved fine tile seams.
Extra or changed positions require a new independent structure proof.

Raw flat-normal comparison uses 0.001 degrees. This proof is not silently applied
to decoder normals; the delivery pipeline separately checks its explicit normal
equivalence policy. Passing position preservation carries exact closure,
orientation and positive-component properties, not every possible topology or
physical property.

## Finite question kinds

All selectors use a key, exact label or prefix, optional material, and mandatory
`expected_count`. Repeated selectors may not duplicate a part. Frames specify
`origin_enu_m` and right-handed orthonormal `axes_enu`, with rows local u, v, d.
Ray depth is local d; ENU is east, north, up.

- `wall_aperture_projection`: an entire UV polygon must avoid the union of
  actual selected wall triangle projections. Every full selected wall solid
  must lie within the stated depth slab; projecting clipped boundary faces
  alone could miss an enclosing solid and is forbidden. Mandatory opaque wall
  negative-control rays establish real surrounding material. This is wall-only;
  glass/frame/context controls are separate.
- `ray_intervals`: actual outward crossings yield separate closed-solid depth
  intervals. Disconnected intervals are never replaced by a min/max envelope.
  Ambiguous edge/tangent crossings cannot pass. Points and depth limits are
  explicitly finite; clear sampled lines do not prove whole-building clearance.
- `support_each`: each specified left part needs a real local joint to a right
  part. Four actual affine top/bottom facets are intersected, then the actual
  ray must match those individual interval bounds. Default `positive_volume`
  requires a positive-area cell with strictly overlapping interiors. Explicit
  `volume_or_exact_area` additionally allows a positive-area opposing surface
  coincidence, with all cell vertices within 1e-9 m numerical plane tolerance.
  This is not a general accepted air-gap tolerance. Point/line-only contact
  cannot pass. Excluded parallel facets, attempted cells and ambiguous witnesses
  are reported. A missing witness is not a universal floating-geometry proof.
- `measure_part_extents`: actual bounds in the stated frame are compared with
  explicit reconstruction limits, e.g. real glass/frame thickness. Bounds are
  not represented as measured dimensions of the real building.
- `closed_plane_sections`: actual triangle/plane intersections must form valid
  simple positive-area closed loops. Endpoint merge is explicit and bounded to
  at most 1e-6 m on computed section endpoints only. On-vertex/coplanar stations
  remain unresolved rather than being silently shifted. This is not a global
  self-intersection or smoothness proof.

`test_synthetic.py` contains small adversarial reviewer fixtures, including
negative separate shells, omitted faces, separated solid intervals, a real wall
hole, wall negative controls, strict volume contact, exact area contact and a
rejected micrometre air gap. These are not building acceptance results.

## Building-specific scope awaiting actual requests

Library: actual facade wall holes, tilted west/south glazing reveal and depth,
entry undercroft rays and negative controls, two tall columns and three low
east columns, six F5 terrace columns, F6 open pergola, curved entrance canopy
and its ribs/posts, two open west terrace end apertures, stepped floor bounds,
and the estimated raised roof volume. All dimensions not sourced as measured
remain reconstruction estimates. Retained source owner 375 and six other
neighbors must remain independently checked by source integration; a tiny
existing source sliver is not permission to edit either source ring.

Museum: five distinct actual curtain-wall levels, entry cut and distinct leaf
placement, curved lower/upper roof shells and their seam, projecting floor/deck
contacts, three curved yellow ribbons, open louvre blades and anchors, stairs
and balustrades, and the north C-shaped wrapped structural spine with five
real glazed slots. Curve knots alone are not a surface-continuity proof. Actual
finite cross-sections, selected seam rays and connected local joints are used;
official height/cantilever scope conflicts stay outside geometric acceptance.

Native image comparison, real browser placement/controls, retained-neighbor
identity, height uncertainty, photo attribution and final registration are
separate required review stages, never implied by a geometric PASS.
