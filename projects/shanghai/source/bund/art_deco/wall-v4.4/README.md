# Bund 19, 20 and 23 structural wall repair

This package repairs source-defined rectangular structural wall panels in the three existing Art Deco reconstructions. Adjacent panels previously retained internal overlapping side faces. The repair emits the boundary of their combined volumes, including real opening edges and real depth steps. Bund 20's recessed spandrels remain **0.12 m behind** the adjoining main wall. Arched and circular fronts, glazing, frames, inscriptions, roofs and independent ornament retain their original geometry.

This is a topology repair of photograph-proportioned models, not a new survey or photogrammetric reconstruction. The existing geographic anchors and full-size bounds are retained. It does not claim to remove every intersection between decorative parts.

## Rebuild

Requirements: Blender 4.3.2, Python 3 with NumPy, and gltfpack 1.3. Use a new output directory. From this directory:

```sh
python rebuild.py --workdir /tmp/bund-wall-rebuild --blender blender --gltfpack /path/to/gltfpack
```

To additionally compare the actual viewer-decoded full models and measure all raw/web/LOD bounds, append `--project /path/to/shanghai`. That project must contain its existing `vendor/three.module.js`, `GLTFLoader.js`, `BufferGeometryUtils.js`, and `meshopt_decoder.module.js`; Node.js is required. These checks run the real loader and decoder without a browser. The models contain no images or textures.

The package freezes the original raw/native models and generator inputs in `baseline/` and `baseline-source/`. `baseline-manifest.json` records their byte sizes and SHA-256 hashes, along with the historical metadata. `arguments.py` verifies them before rebuilding. Generated files go under the supplied work directory; the project is not overwritten. The historical native files retain the original lettering as mesh geometry. The original font and its OFL attribution are also included with the generator.

The pipeline identifies wall faces through the original generator calls, checks their exact face order against the frozen native meshes, groups their original directions and planes, unions their occupied volumes, and replaces only those selected faces. It uses the original front, back and setback depths. The other native face positions, face order, material indices, smoothing and UVs are hashed before and after. Opening rays, closed-shell edge incidence, winding, signed volume, original transforms, bounds and retained front-depth areas are checked.

## Export and measurements

Native meshes preserve the original non-wall faces, including pre-existing degenerate faces. Before GLB compression, the export removes **exactly zero-area** index triples, using the cross product of the original FLOAT32 positions evaluated in FLOAT64, without an area epsilon. It preserves the original attribute bytes and every nondegenerate exported triangle. This removes 94, 139 and 1,454 zero-area triangles from Bund 19, 20 and 23 respectively; the counts include 3 new wall export degeneracies in Bund 20 and 2 in Bund 23. Native files are not changed by that normalization.

Web compression uses `-cc -noq -km -ke`. Far LOD additionally uses `-si 0.35 -se 0.002 -sp`. Copyright and source notes are restored after gltfpack. No `-kn` or position quantization option is used.

| Model | Native triangles | Raw/web triangles | Far LOD triangles | Maximum decoded raw/web position difference |
| --- | ---: | ---: | ---: | ---: |
| Bund 19 | 159,522 | 159,428 | 65,776 | 0 m |
| Bund 20 | 251,454 | 251,315 | 125,642 | 0.000003821 m |
| Bund 23 | 195,186 | 193,732 | 79,686 | 0.000015164 m |

Full-model comparisons match oriented triangles one-to-one by material, preserving winding and counts. Bund 19 uses exact world-coordinate matching. Bund 20 and 23 allow a measured 0.0001 m tolerance for Float32 transform serialization; their actual maxima appear above. Maximum normal differences are below 0.013 degrees. Raw/web used-vertex bounds differ by 0, 0 and 0.000001407 m respectively. Far LOD bounds differ from raw by 0, 0 and 0.017612145 m respectively. Those are numerical export/LOD differences, not estimates of real-world dimensional accuracy.

`validation/` contains the measured native-preservation, surface, decoder, compression and final asset reports. The preservation reports describe the pre-normalization export explicitly; the final asset reports bind the released files to SHA-256 hashes. `portable-rebuild-validation.json` records the separate clean-directory rebuild and its output comparisons. Blender native files may contain save-session metadata, so byte-identical `.blend` output is not promised.

## Attribution

The architectural reconstruction and repair source retain the project's MIT attribution (`LICENSE`). Building footprints and geographic provenance remain © OpenStreetMap contributors, ODbL-1.0. This does not relicense OSM-derived geographic data as MIT. The original photographic references and their individual authors/licenses remain documented in `baseline-source/references.json` and the historical landmark records. They are used as references and are not embedded in these models. The bundled inscription font has its separate SIL Open Font License in `baseline-source/assets/OFL.txt`.
