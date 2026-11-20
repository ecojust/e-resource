"""Verify the serialised west gate, including its cut-through passage and closed leaves."""
from pathlib import Path
import argparse
import hashlib
import json
import runpy
import numpy as np


def check(scene):
    results = []

    def ray(name, start, direction, expected, low, high):
        hit = scene.ray(start, direction, 18)
        if expected is None:
            assert hit is None, (name, hit)
            results.append({'part': name, 'origin': start, 'direction': direction, 'clear': True})
        else:
            assert hit and hit['material'] in expected and low < hit['distance_m'] < high, (name, hit)
            results.append({'part': name, 'origin': start, 'direction': direction, **hit})

    for x in (-2.13, 2.13):
        for z in (.31, 1.33, 3.67):
            ray('dressed stone side of opening', [x, -2, z], [0, 1, 0], {'grey stone'}, 1.98, 2.04)
    for x in (-.71, .71):
        for z in (.19, .63, 2.55):
            ray('recessed rail of closed iron leaf', [x, -2, z], [0, 1, 0], {'painted iron'}, 2.55, 2.64)
    for x in (-1.33, .44, .69):
        ray('sight line above closed leaves into old lane', [x, -2, 3.78], [0, 1, 0], None, 0, 0)
    for x in (-.47, .55):
        ray('stone lintel over the gate', [x, -2, 4.23], [0, 1, 0], {'grey stone'}, 1.98, 2.04)
        ray('upper window recessed glass', [x, -2, 6.73], [0, 1, 0], {'window glass'}, 2.21, 2.27)
        ray('upper window transom', [x, -2, 7.72], [0, 1, 0], {'window hardwood'}, 2.12, 2.22)
    for x in (-.379, .379):
        ray('two wooden mullions', [x, -2, 6.72], [0, 1, 0], {'window hardwood'}, 2.12, 2.22)
    ray('upper window sill', [.41, -2, 5.784], [0, 1, 0], {'dressed stone'}, 1.87, 1.94)
    ray('tablet raised border', [-1.145, -2, 5.27], [0, 1, 0], {'dressed stone'}, 1.92, 1.95)
    ray('tablet ground', [-1.02, -2, 5.25], [0, 1, 0], {'inset inscription'}, 1.95, 1.99)
    for x in (-.54, .54):
        ray('crest of stepped parapet', [x, .45, 12], [0, 0, -1], {'door soffit', 'grey stone'}, 1.47, 1.51)
    ray('lower step', [1.34, .49, 12], [0, 0, -1], {'door soffit', 'grey stone'}, 2.00, 2.04)
    ray('green enameled street number plate', [2.174, -2, 2.251], [0, 1, 0], {'street plaque'}, 1.95, 1.99)
    ray('soffit inside portal', [.34, .79, 2], [0, 0, 1], {'door soffit'}, 1.92, 1.96)
    for name,material,count,lo,hi in [('three lane name glyphs','lettered stone',3,4.85,5.65),
                           ('enamel plate characters','street plaque lettering',7,2.08,2.37)]:
        tris = scene.tri[scene.mi == scene.materials.index(material)]
        assert len(tris) > count * 8 and lo < tris[:, :, 2].min() < tris[:, :, 2].max() < hi, name
        results.append({'part': name, 'material': material, 'triangles': len(tris),
                        'bounds': [tris.min((0,1)).tolist(), tris.max((0,1)).tolist()]})
    return results


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    for k in ('project', 'manifest', 'decoded', 'out'):
        parser.add_argument('--' + k, type=Path, required=True)
    args = parser.parse_args()
    sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
    load = runpy.run_path(str(args.project / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    manifest = json.loads(args.manifest.read_bytes())
    variants = []
    for role in ('raw', 'full', 'lod'):
        asset = manifest['assets'][role]
        encoded = args.manifest.parent / asset['file']
        assert sha(encoded) == asset['sha256']
        model = encoded if role == 'raw' else args.decoded / (role + '.glb')
        scene = load['SerialScene'](model)
        assert len(scene.tri) == asset['triangles']
        variants.append({'role': role, 'file': asset['file'], 'sha256': sha(encoded),
                         'decoded_sha256': sha(model), 'triangles': len(scene.tri), 'samples': check(scene)})
    args.out.write_text(json.dumps({'id': manifest['id'], 'passed': True, 'variants': variants,
        'manifest_sha256': sha(args.manifest), 'script_sha256': sha(Path(__file__)),
        'count': sum(len(v['samples']) for v in variants)}, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    run()
