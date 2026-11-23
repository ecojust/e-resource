"""Use fixed, native-2016 photo pixels to inspect the visible material in the serialized No. 3 court."""
import argparse
import hashlib
import json
from math import cos, pi, sin
from pathlib import Path
import sys

from register_court import Camera

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene


def measure(mesh):
    scene, cam = SerialScene(mesh), Camera()
    control = json.loads((HERE / 'terrace-photo-control.json').read_text())
    results = []
    for p in control['native_photo_readings']:
        xy, target = p['native_pixel'], p['expected']
        hit = scene.ray(cam.c, cam.ray(xy), 50.)
        actual = None if hit is None else hit['material']
        nearby = 0 if actual == target else None
        if nearby is None:
            for radius in (2, 4, 8, 12, 18, 24, 32):
                for i in range(12):
                    angle = i*2*pi/12
                    q = [xy[0]+radius*cos(angle), xy[1]+radius*sin(angle)]
                    other = scene.ray(cam.c, cam.ray(q), 50.)
                    if other and other['material'] == target:
                        nearby = radius
                        break
                if nearby is not None:
                    break
        results.append(dict(facet=p['facet'], photo_pixel=xy, expected=target, first_hit=actual,
                            same_material=actual == target, hit_xyz=None if hit is None else hit['point_enu_m'],
                            first_tested_matching_ring_px=nearby))
    return dict(mesh=mesh.name, sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(), photo='2016 Dafu Li Shanghai.JPG',
                full_image_pixels=[4912,3264], exact_material_hits=sum(v['same_material'] for v in results),
                rays=len(results), samples=results)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh', type=Path)
    p.add_argument('output', type=Path)
    args=p.parse_args()
    result=measure(args.mesh)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    print(result['exact_material_hits'], result['rays'])
