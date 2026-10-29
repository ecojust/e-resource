# 四行仓库与大陆银行仓库复合体

This is a photo-informed exterior model of the complete adjoining warehouse
compound, built from public photographs, the SIADR project description and
manually interpreted published designer diagrams. It is not a measured survey.

The independent 20 m plan-scale trace is rigidly registered to the frozen OSM /
Overture owner. It is not stretched to the source polygon. Source ownership and
the interpreted architectural boundary have different purposes. The agreement
diagnostics in calibration.json are not measurement accuracy estimates.

The modeled exterior has five main floors and a set-back sixth floor. The
project's published nominal height is 27.7 m. The removed later seventh floor
is absent. The south face contains ten western and eight eastern ordinary
window bays, separated by distinct deep entry recesses; the east end has three
window bays. The north boundary follows the curved plan trace. Two plan voids
receive framed transparent skylights; they are not asserted to be two fully
independent surveyed courtyards. Article-documented entrance glass canopies are
present, with their detailed shape and height marked as estimates.

The west wall retains masonry around seven photo-traced, dark-glass-backed
damage openings and one brick-backed deep recess. The concrete remnants and
lower exposed brick are not converted into one giant opening. The 65 small
dark marks are photograph-selected approximations, not a claim that every
historical bullet hole has been individually reconstructed. Their physical
depths and the dimensions behind the west-wall surface remain estimates.

Window steel grids, separate glass cells, reveals, plaster relief, brick
infill and borders, exposed damage thickness, roof parapets, skylight frames,
entrance returns, lettering and bounded roof equipment are actual geometry.
No photograph is embedded as a texture. Northern hidden details, exact pane
counts, glazing finish, service equipment and original typeface are estimates.

## Build

Use Python 3 with NumPy, Shapely 2.1 and fontTools. Each output path must be new.

```sh
python build_model.py --out /new/raw
python build_model.py --lod --out /new/authored-lod
blender -b -t 2 --python render_previews.py -- --glb /new/raw/jingan-sihang-warehouse.glb --output /new/native
```

The authored LOD removes only labels matching
`^fine-masonry-joint/[0-9]+$`: these are 3 mm surface mortar seams. All
windows, glazing, damage openings, structural remnants, small observed pits,
signage, atria and roof volumes remain. The raw sidecar records the actual
serialized triangle ranges per material primitive, allowing independent
decoding and feature verification. Compressed output must be independently
decoded; raw triangle indices must not be assumed to survive compression.

Source-freeze.json binds this source and the included licensed reference
files. Private designer article images are neither included nor read by the
builder. Public reference-image licenses and view records are recorded in
photo-reference-register.json. The font is a small Noto CJK TC Bold subset;
its SIL OFL license travels in fonts/.

Every deliverable file must remain strictly below 100 MB. Target
budgets are raw 40 MB, web 15 MB, authored LOD 5 MB and native 30 MB; these are
engineering targets, not substitutes for actual exported size checks.
Geometry previews and author metadata do not constitute root visual or
browser acceptance.

Geometry and code: MIT. Frozen geographic source: OpenStreetMap contributors
and Overture Maps, ODbL-1.0. Individual referenced photographs retain their
listed CC0, CC BY 4.0 or CC BY-SA 4.0 licenses. Font: SIL OFL 1.1.
