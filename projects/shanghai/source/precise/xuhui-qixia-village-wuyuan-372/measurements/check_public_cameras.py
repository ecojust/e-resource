"""Verify the four original optical projections and the visible first surfaces in all nine page views."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

from render_public_cameras import projection
from register_court import Camera

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

def glz(value):
    return 'Qixia | muted steel-blue glazing' if value == 'window' else value

def picks():
    controls = {}
    for frame, name in [(17, 'no6-loggia'), (18, 'no7-enclosure')]:
        data = json.loads((HERE / (name + '-photo-controls.json')).read_bytes())
        for feature, pixel, role in data['probes']:
            controls[feature] = [frame, pixel, data['materials'].get(role, role)]
    controls.update({
        'unnumbered upper west glass': [19, [235, 84], glz('window')],
        'unnumbered middle east glass': [19, [301, 213], glz('window')],
        'unnumbered single middle glass': [19, [111, 262], glz('window')],
        '9 upper slab': [20, [325, 97], 'Qixia 9 | blue grey concrete balcony slab'],
        '9 middle slab': [20, [368, 260], 'Qixia 9 | blue grey concrete balcony slab'],
        '9 left plate': [20, [114, 384], 'Qixia 9 | green address enamel']})
    return controls

VIEWS = {
    'overview': ['yellow apron mid', 'upper middle light','unnumbered upper west glass','9 middle slab'],
    'station-17': ['upper slab left','yellow apron mid','second pale leaf','upper red cheek','upper canopy thin red face'],
    'station-18': ['upper left light','upper middle light','upper centre heavy upright','lower slab front near middle'],
    'station-19': ['unnumbered upper west glass','unnumbered middle east glass','unnumbered single middle glass'],
    'station-20': ['9 upper slab','9 middle slab','9 left plate'],
    'six-windows': ['yellow apron mid','second pale leaf','upper red cheek','upper canopy thin red face'],
    'green-rail': ['upper left light','upper centre heavy upright','lower substantial right glazing'],
    'east-high':['yellow apron mid','upper middle light','unnumbered upper west glass','9 middle slab'],
    'west-high':['9 upper slab','9 middle slab','unnumbered middle east glass']}

def image(matrix, points):
    points = np.atleast_2d(points)
    out = np.column_stack([points, np.ones(len(points))]) @ matrix.T
    return out[:, :2] / out[:, 2:3]

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def evaluate(mesh, reference, camera_path):
    scene = SerialScene(mesh)
    anchor_scene = scene if mesh.samefile(reference) else SerialScene(reference)
    views = json.loads(camera_path.read_bytes())
    anchors = {}
    controls = picks()
    for label in sorted({key for names in VIEWS.values() for key in names}):
        frame, pixel, expected = controls[label]
        camera = Camera(frame)
        hit = anchor_scene.ray(camera.c,camera.ray(pixel),100)
        anchors[label] = dict(frame=frame,pixel=pixel,expected=expected,photo_first_hit=hit)
    checks = []
    exact = []
    extents = {}
    vertices = scene.tri.reshape(-1,3)
    grid = np.array([[120,80],[325,240],[540,400],[610,75],[70,420]])
    for view in views:
        matrix = projection(view)
        key = view['name']
        eye = np.array(view['eye'])
        pixels = np.array([view['width'],view['height']])
        if key in ('overview','east-high','west-high'):
            uv = image(matrix,vertices) / pixels
            extents[key] = [uv.min(axis=0).tolist(),uv.max(axis=0).tolist()]
        if view.get('photo_id'):
            c = Camera(int(view['photo_id'])%100)
            xyz = [c.c + c.ray(pixel)*7. for pixel in grid]
            error = np.linalg.norm(image(matrix, xyz)-grid,axis=1)
            exact.append(dict(station=key,original_pixels=grid.tolist(),
                              max_reprojection_error_px=float(error.max()),eye_error_m=float(np.linalg.norm(eye-c.c))))
        for label in VIEWS[key]:
            a = anchors[label]
            source_hit = a['photo_first_hit']
            mark = dict(view=key,feature=label,source_station=a['frame'],source_pixel=a['pixel'],expected=a['expected'],
                        reference_material=source_hit['material'] if source_hit else None,passed=False)
            if source_hit:
                target=np.array(source_hit['point_enu_m'])
                uv=image(matrix,target)[0] / pixels
                hit=scene.ray(eye,target-eye,100)
                offset=float(np.linalg.norm(np.array(hit['point_enu_m'])-target)) if hit else None
                mark.update(image_fraction=uv.tolist(),first_hit=hit,separation_m=offset,reference_xyz=target.tolist(),
                            passed=bool(source_hit['material']==a['expected'] and hit and hit['material']==a['expected']
                                        and offset<.04 and np.all((uv>0)&(uv<1))))
            checks.append(mark)
    return dict(file=mesh.name,sha256=sha(mesh),reference_sha256=sha(reference),cameras_sha256=sha(camera_path),
                camera_registration_sha256=sha(HERE/'court-cameras.json'),historical_views=exact,
                working_distance_limit_m=100,tolerance_m=.04,all_vertices_fraction=extents,
                count=len(checks),matched=sum(c['passed'] for c in checks),checks=checks)

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--reference',type=Path)
    p.add_argument('--cameras',type=Path,default=HERE.parent/'source/cameras.json')
    args=p.parse_args()
    result=evaluate(args.mesh,args.reference or args.mesh,args.cameras)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['matched'], '/',result['count'])
