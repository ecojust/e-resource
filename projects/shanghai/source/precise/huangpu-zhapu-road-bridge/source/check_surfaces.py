"""Check the photographed bridge features in the delivered GLBs and the reopened Blender file."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
MODEL = 'huangpu-zhapu-road-bridge'
FONT = SOURCE / 'fonts/ZhapuBridgeSigns.otf'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
GLBScene = runpy.run_path(str(READER))['SerialScene']
PANELS = tuple(zip('乍浦路桥', (9.1, 3.05, -3.05, -9.1)))
SIZE = 192


def digest(file):
    return sha256(file.read_bytes()).hexdigest()


def extract_native(blend, output):
    import bpy
    bpy.ops.wm.open_mainfile(filepath=str(blend.resolve()))
    triangles, material_ids, materials, objects = [], [], [], []
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        mesh = obj.data
        mesh.calc_loop_triangles()
        points = np.array([v.co[:] for v in mesh.vertices])
        transform = np.asarray(obj.matrix_world)
        world = points @ transform[:3, :3].T + transform[:3, 3]
        ids = []
        for face in mesh.loop_triangles:
            material = obj.material_slots[face.material_index].material.name
            if material not in materials:
                materials.append(material)
            ids.append(materials.index(material))
        triangles.append(world[[t.vertices[:] for t in mesh.loop_triangles]])
        material_ids.extend(ids)
        objects.append(obj.name)
    np.savez_compressed(output, triangles=np.concatenate(triangles), ids=material_ids,
             materials=materials, objects=objects, blender=bpy.app.version_string)


class NativeScene:
    ray = GLBScene.ray

    def __init__(self, file):
        with np.load(file) as data:
            self.tri = data['triangles']
            self.mi = data['ids']
            self.materials = data['materials'].tolist()
            self.lows = self.tri.min(axis=1)
            self.highs = self.tri.max(axis=1)
            self.objects = data['objects'].tolist()
            self.blender = str(data['blender'])


def reference_masks():
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(str(FONT), 600)
    masks = {}
    for char, _ in PANELS:
        sample = Image.new('L', (850, 850))
        ImageDraw.Draw(sample).text((20, 20), char, font=font, fill=255)
        crop = sample.getbbox()
        assert crop, char
        masks[char] = np.asarray(sample.crop(crop).resize((SIZE, SIZE), Image.Resampling.LANCZOS)) > 127
    return masks


def surface_mask(triangles, center_y, center_z):
    """Project actual letter triangles as seen from the upstream bank, with north on the left."""
    from PIL import Image, ImageDraw
    raster = Image.new('1', (SIZE, SIZE))
    draw = ImageDraw.Draw(raster)
    for tri in triangles:
        x = (.5 + (center_y - tri[:, 1]) / .50) * SIZE
        y = (.5 + (center_z - tri[:, 2]) / .48) * SIZE
        draw.polygon(list(zip(x.tolist(), y.tolist())), fill=1)
    return np.asarray(raster, dtype=bool)


def similarity(a, b):
    return float(np.count_nonzero(a & b) / np.count_nonzero(a | b))


def examine(scene, role, masks):
    from scipy.ndimage import distance_transform_edt
    rays = []

    def ray(label, origin, direction, length, material=None, distance=None):
        hit = scene.ray(origin, direction, length)
        good = hit is None if material is None else bool(hit and hit['material'] == material)
        if good and distance is not None:
            good = distance[0] <= hit['distance_m'] <= distance[1]
        rays.append(dict(label=label, origin=origin, direction=direction, length_m=length,
                         expected_material=material, distance_interval_m=distance, hit=hit, passed=bool(good)))

    for y, name, soffit in [(-27, 'south opening', 2.57), (0, 'central opening', 3.38), (27, 'north opening', 2.57)]:
        deck = 4.21 - .47 * (y / 35.97) ** 2
        for level in (.24, 1.45):
            ray(name + ' through the river opening', [-12, y, level], [1, 0, 0], 24)
        ray(name + ' underside', [.6, y, 0], [0, 0, 1], 6, 'river concrete', [soffit - .18, soffit + .12])
        ray(name + ' carriageway centre', [0, y, 9], [0, 0, -1], 7, 'asphalt', [9 - deck - .04, 9 - deck + .04])
        for side in (-1, 1):
            def down(label, x, material, level):
                ray(name + ' ' + label, [side*x, y, 9], [0, 0, -1], 7, material, [9-level-.05, 9-level+.05])
            down('carriageway inside curb', 6.38, 'asphalt', deck)
            down('curb', 6.51, 'curb stone', deck+.166)
            down('pedestrian paving', 7.54, 'paved walk', deck+.16)
            down('parapet cap', 8.53, 'projecting coping', deck+1.10)
            for height in (.27, .58, .88):
                ray(name+' solid parapet face', [side*12, y, deck+height], [-side, 0, 0], 4,
                    'painted fascia', [3.31, 3.39])
            ray(name+' above parapet', [side*12, y, deck+1.29], [-side, 0, 0], 24)
            ray(name+' fascia over river', [side*12, y, soffit+.40], [-side, 0, 0], 4,
                'painted fascia', [3.28, 3.39])
    for y in (-18.29, 18.29):
        for side in (-1, 1):
            ray('exposed pier plinth end', [side*12, y, .20], [-side, 0, 0], 4, 'cutwater stone', [2.74, 2.84])
            ray('sloping pier nose', [side*12, y, 1.15], [-side, 0, 0], 4, 'cutwater stone', [2.38, 2.62])
            ray('water clear beside the pier', [side*12, y+1.80, .20], [-side, 0, 0], 24)
        ray('pier beneath roadway', [.22, y-3, .18], [0, 1, 0], 5, 'cutwater stone', [1.74, 1.85])

    letters = []
    if 'panel lettering' in scene.materials:
        letters = scene.tri[scene.mi == scene.materials.index('panel lettering')]
    signs = []
    for char, y in PANELS:
        z = 4.21 - .47 * (y / 35.97) ** 2 - .18
        ray('green name plate margin '+char, [-12, y+.39, z-.25], [1, 0, 0], 4,
            'green name panels', [3.21, 3.29])
        faces = np.asarray([tri for tri in letters if abs(tri[:, 1].mean()-y) < .6])
        mask = surface_mask(faces, y, z)
        fits = {c: round(similarity(mask, reference), 5) for c, reference in masks.items()}
        matched = (max(fits, key=fits.get) == char and fits[char] >= .88)
        expected = masks[char]
        for ink in (False, True):
            depth = distance_transform_edt(expected if ink else ~expected)
            for half_y in (0, SIZE//2):
                for half_x in (0, SIZE//2):
                    region = depth[half_y+7:half_y+SIZE//2-7, half_x+7:half_x+SIZE//2-7]
                    pixel_y, pixel_x = np.unravel_index(np.argmax(region), region.shape)
                    if region[pixel_y,pixel_x] < 2.5:
                        continue
                    u, v = (half_x+7+pixel_x+.5)/SIZE, (half_y+7+pixel_y+.5)/SIZE
                    material = 'panel lettering' if ink and role != 'lod' else 'green name panels'
                    ray(char + (' stroke' if ink else ' counter or background'),
                        [-12, y+(.5-u)*.50, z+(.5-v)*.48], [1, 0, 0], 4, material,
                        [3.218, 3.233] if material=='panel lettering' else [3.231, 3.25])
        signs.append(dict(character=char, station_y_m=y, projected_triangles=len(faces),
                          font_silhouette_iou=fits, silhouette_pixels=int(mask.sum()),
                          passed=bool(not mask.any() if role=='lod' else matched)))
    for side in (-1, 1):
        # The central paving joint at this real station is removed in the simplified mesh.
        ray('paving joint detail', [side*7.4, -18.29+36.58/15, 9], [0, 0, -1], 7,
            'paved walk' if role=='lod' else 'recessed moulding')
    count = {m: int((scene.mi==i).sum()) for i,m in enumerate(scene.materials) if (scene.mi==i).any()}
    return dict(passed=all(r['passed'] for r in rays) and all(s['passed'] for s in signs),
                triangles=len(scene.tri), triangles_by_material=count, rays=rays, name_panels=signs)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=PROJECT/'assets/models/candidates'/MODEL/'manifest.json')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--work', type=Path)
    parser.add_argument('--blender', default='blender')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_bytes())
    if manifest['id'] != MODEL:
        raise ValueError('Wrong model manifest')
    results, masks = {}, reference_masks()
    for role in ('raw', 'full', 'lod', 'native'):
        entry = manifest['assets'][role]
        packed = args.manifest.parent / entry['file']
        assert digest(packed)==entry['sha256'] and packed.stat().st_size==entry['bytes']
        with TemporaryDirectory(dir=args.work) as scratch:
            if role == 'native':
                file = Path(scratch)/'scene.npz'
                subprocess.run([args.blender,'-b','-t','1','--python-exit-code','1','-P',__file__,'--',
                                '--extract-native',str(packed),str(file)],check=True,stdout=subprocess.DEVNULL)
                scene = NativeScene(file)
            else:
                file = packed
                if role != 'raw':
                    file = Path(scratch)/'decoded.glb'
                    subprocess.run(['node',UNPACK,packed,file,DECODER],check=True,stdout=subprocess.DEVNULL)
                scene = GLBScene(file)
            result = examine(scene, role, masks)
            if role=='native':
                result.update(blender=scene.blender, editable_meshes=len(scene.objects))
            else:
                assert result['triangles']==entry['triangles']
            results[role] = dict(sha256=entry['sha256'], **result)
    near = results['raw']['triangles_by_material']
    for role in ('full','native'):
        assert results[role]['triangles_by_material']==near
    assert results['lod']['triangles'] < results['full']['triangles']
    report = dict(id=MODEL, passed=all(r['passed'] for r in results.values()),
                  manifest_sha256=digest(args.manifest), checker_sha256=digest(Path(__file__)),
                  independent_glb_reader_sha256=digest(READER), font_sha256=digest(FONT),
                  meshopt_decoder_sha256=digest(DECODER), variants=results)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
    for role,row in results.items():
        failures=[(r['label'],r['hit']) for r in row['rays'] if not r['passed']]
        print(role,row['triangles'],len(row['rays']),[s['font_silhouette_iou'][s['character']] for s in row['name_panels']],failures)
    return report['passed']


if __name__ == '__main__':
    if '--extract-native' in sys.argv:
        extract_native(*map(Path, sys.argv[sys.argv.index('--extract-native')+1:]))
    else:
        raise SystemExit(0 if main() else 1)
