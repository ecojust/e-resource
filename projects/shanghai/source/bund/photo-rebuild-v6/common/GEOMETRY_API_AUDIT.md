# Shared geometry API audit

`python test_photo_architecture.py` passed 38 lightweight checks. It creates only temporary small GLBs, then reads their actual binary accessors; it does not run Blender, rendering or a browser. `geometry-api-audit.json` pins the exact source hashes and records individual results.

Checks cover continuous wall skins with rectangular windows, arched windows and a door notch; zero triangle area inside the openings; triangulated front area; volume equal to net wall area times thickness; exact position-welded manifold edges and consistent winding. The same checks cover rotated walls at a 1.2 km coordinate offset and their serialized FLOAT32 GLBs. Other cases include both handednesses of box bases, courtyard and multiple-island prisms, united window frame grids, horizontal/vertical/diagonal/bent tubes, columns with zero-radius cap vertices, and stepped column profiles. The exported axes are explicitly tested as `[east, up, -north]`, with positive signed volume and normals aligned to the serialized triangle geometry.

Fixes made during review:

- Window border, mullions and transoms are united in 2D before one extrusion, removing overlapping front faces and opposing interior end faces. All now use the existing border's depth interval `[-0.27, -0.16]` m; the previous bars had a slightly different interval. Labels use `-frame-grid` instead of individual `-mullion` / `-transom` solids.
- Polygon extraction ignores lower-dimensional remnants from clipping. Invalid mapper handedness, zero-length façades, singular box bases, repeated/reversing tube points, invalid radii/segment counts and reversed lathe profiles fail explicitly.
- Exported normals are calculated from the actual FLOAT32 positions. A triangle that collapses when serialized now fails export instead of leaving an invalid solid.

API conventions remain unchanged: `Facade(a,b)` expects a directed **CCW outer footprint edge**, with its right-hand horizontal normal pointing outward. A prism mapper uses `(u, z, d)` with `u × z` pointing toward positive `d`. `Facade.box` uses a reflected basis and the helper reverses winding correctly. The per-building input files supplied here retain CCW OSM outer rings.

Manifold assertions apply to each generated solid, not a Boolean union of an entire building with every intersecting ornament. They do not prove that arbitrary curved tube paths avoid self-intersection or that architectural proportions match photographs. Those remain checks for each building. `blender_finish.py` passed syntax and axis-contract review; its actual Blender import and optional render were not run during this audit.
