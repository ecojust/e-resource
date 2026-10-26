# Bund 18: proportion correction and limited photographic appearance

The mapped footprint and WGS84 anchor stay the same. Real wall openings, columns, window frames, cornices, roof, side and rear meshes remain three dimensional. `geometry-changes.json` records the revised photo-proportioned central bay/column spacing, window widths, side-window and pediment levels, and 1.037 vertical factor. These are photo-based estimates, not surveyed dimensions; neither decimal precision nor matching the mapped footprint proves ground-truth accuracy.

Only selected lower front limestone faces and six central window interiors use the original photo. The six glazing rectangles have separate four-corner UV mappings; their physical bronze frames are retained. Attic, columns, frames, reliefs, cornices, side, rear and roof keep geometric materials. Regions intersecting known street-light/cabinet masks stay untextured. `photo-control-points.json` records coordinates and limitations. The photo is embedded byte for byte without cropping, retouching or regeneration. Photo shading and reflections remain in the colour, so this is not calibrated PBR albedo or photogrammetry.

Photo: **ScareCriterion12**, “上海外滩麦加利银行旧址2021.jpg”, **CC BY-SA 4.0**. [Original page](https://commons.wikimedia.org/wiki/File:%E4%B8%8A%E6%B5%B7%E5%A4%96%E6%BB%A9%E9%BA%A6%E5%8A%A0%E5%88%A9%E9%93%B6%E8%A1%8C%E6%97%A7%E5%9D%802021.jpg), [license](https://creativecommons.org/licenses/by-sa/4.0/).

The photographic GLB / native model derivative is distributed under **CC BY-SA 4.0**. Original modeling code retains the project's **MIT** license. OSM footprint and its derived spatial data retain **ODbL 1.0**, © OpenStreetMap contributors. Raw/web/LOD GLBs carry standalone copyright, source and license links. Each includes the original 798,956-byte JPEG, SHA-256 `26a1219fe534659ae78bae9dfc498aef30b50b957172046a5c401906758315ba`; native `.blend` packs it too.

## Rebuild

Install this package as `source/bund/chartered_bank/photo-v4.3/`, next to the existing `building-source.json` and `photo-source.json`. Run from the Shanghai project root with Blender 4.3 and gltfpack 1.3:

```sh
blender --background --threads 2 --python source/bund/chartered_bank/photo-v4.3/build_geometry.py -- --output exported/bund18-geometry
blender --background --threads 2 --python source/bund/chartered_bank/photo-v4.3/apply_photo.py -- --input exported/bund18-geometry/chartered-bank.blend --output exported/bund18-photo --render
python source/bund/chartered_bank/photo-v4.3/compress_models.py --input exported/bund18-photo/bund18-photo.glb --output exported/bund18-photo
python source/bund/chartered_bank/photo-v4.3/validate_assets.py --directory exported/bund18-photo
```

`--render` is optional. `--photo` can specify the original JPEG; otherwise it is found under the project `assets/references/bund/bund18.jpg`. `--gltfpack` accepts a tool path if it is not on PATH.

The development-only `prepare_geometry.py` is not part of the relocatable source package; `build_geometry.py` is standalone with the frozen parent JSON inputs. The chosen output directory may differ from published asset names.

The full web model uses `-cc -noq -km -ke`; distant LOD additionally uses `-si 0.35 -se 0.002 -sp`, producing 73,162 versus 128,046 triangles. The ratio is an optimization target, not the actual final reduction. `compress_models.py` explicitly restores copyright removed by gltfpack 1.3; it does not alter the JPEG.

`PhotoFacade_*` materials must skip generic architectural grain and generic glass recolouring/reflections. The photographic appearance is already present in their base-colour map. Runtime/browser validation and publication are separate from the isolated source/asset checks in `asset-audit.json`.
