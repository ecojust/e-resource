"""Inspect each complete GLB against fifty window openings and three photographic views."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / 'source'
sys.path[:0] = [str(SRC), str(HERE.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
import changzhi_sashes as sash


def data(name):
    return json.loads((HERE / name).read_bytes())


def inspect(path):
    scene = SerialScene(path)
    host = data('upper-window-host-layout.json')
    original = data('observed-upper-window-mouths.json')['controls']
    district = data('district-upper-window-mouths.json')['points']
    cameras = data('upper-window-cameras.json')
    shade = [sash.PANE, sash.SKY]
    panels = [sash.COVER, sash.RUSSET]
    structure, photo = [], []

    def first(eye, direction, allowed, **fields):
        h = scene.ray(eye, direction, 200.)
        material = h['material'] if h else None
        return dict(**fields, eye=np.round(eye,5).tolist(), direction=np.round(direction,8).tolist(),
                    allowed=allowed, first=material, matched=material in allowed,
                    point=np.round(h['point_enu_m'],5).tolist() if h else None,
                    triangle=int(h['triangle_index']) if h else None)

    def photo_ray(key, points, camera, expected):
        cam = cameras[camera]
        # Interior sample fixed by the original left/right spring and sill, before measuring any ray.
        l = np.asarray(points['spring_left']) * .46 + np.asarray(points['sill_left']) * .54
        r = np.asarray(points['spring_right']) * .46 + np.asarray(points['sill_right']) * .54
        uv = l*.61 + r*.39
        ray = np.array(cam['R']).T @ np.linalg.solve(cam['K'], [*(uv*cam.get('native_to_work',[1,1])), 1.])
        photo.append(first(np.asarray(cam['eye']), ray, expected, id=key, camera=camera, uv=uv.round(4).tolist()))

    for item, ctrl in zip(sash._windows(host), original, strict=True):
        row, face, c, w = item
        assert row['id'] == ctrl['id']
        key = row['id']
        lo, spring, hi = [row[k] for k in ('sill','spring','crown')]
        world, sign = sash._mapper(face)
        def sample(s,z,allowed,feature):
            eye = np.asarray(world(s,z,sign*1.2))
            d = np.asarray(world(s,z,0.))-eye
            structure.append(first(eye,d,allowed,id=key,feature=feature,face_sz=[round(s,5),round(z,5)]))
        shape = sash._mouth(c,w,lo,spring,hi)
        case = shape.buffer(-.014,join_style=2)
        light = case.buffer(-min(.058,max(.032,.039*w)),join_style=2)
        l,z0,r,z1 = light.bounds
        sample(c-w/2+.008,lo+.29*(hi-lo),[sash.SHADE],'reveal')
        sample((c-w/2+.014+l)/2,lo+.29*(hi-lo),[sash.CASE],'fixed left case')
        sample(c,lo-.024,[sash.SILL],'sill nosing')
        covered = row['face']=='nanxun' and row['level']==2 and row['axis']>3
        if covered:
            sample(c,lo+.29*(hi-lo),[sash.BOARD_EDGE],'central seam')
            heights = (.15, .48, .81) if row['axis']==6 else (.13, .50, .78)
            for j,fx in enumerate([.25,.75]):
                for k,fz in enumerate(heights):
                    red = row['axis']==6 and (k==0 or k==1 and j==0)
                    red |= row['axis']==4 and k==0 and j==0 or row['axis']==5 and k==0
                    mat=sash.RUSSET if red else sash.COVER
                    sample(l+(r-l)*fx,z0+(z1-z0)*fz,[mat],f'panel {j+1},{k+1}')
            expected = panels+[sash.BOARD_EDGE,sash.CASE]
        else:
            if row['shape']=='round':
                rail = z0+(spring-z0)/3
            elif row['face'].startswith('corner') or row['face']=='nanxun':
                rail = z0+.605*(z1-z0)/3
            else:
                rail = z0+(z1-z0)*.25
            sample(c,z0+(rail-z0)*.62,[sash.STEEL,sash.BEAD],'meeting edge')
            sample(l+.16*(r-l),rail,[sash.STEEL],'horizontal bar')
            sample(l+.10*(r-l),z0+.39*(rail-z0),shade,'left pane')
            sample(r-.10*(r-l),z0+.39*(rail-z0),shade,'right pane')
            expected = shade+[sash.STEEL,sash.BEAD,sash.CASE]
        if key in district:
            # The far edge of Nanxun axis 3 is outside the published picture. Its aperture is partly visible.
            photo_ray(key,district[key],'hk202342',expected)
        camera = ctrl['reference']
        if camera in cameras and camera != 'hk202342':
            photo_ray(key,ctrl['points'],camera,expected)
    # Supplement the original three-camera trial with the independently named view and two
    # rematched January stations. The original, including its earlier errors, remains separately counted.
    before = len(photo)
    supplement = data('named-and-oblique-sash-cameras.json')
    cameras.update({'named66':supplement['named66']})
    for n in ('last-5-256','last-2-216'):
        cameras[n+'-named-control'] = supplement[n]
    def expected(key):
        _,a,l = key.split('/')
        return panels+[sash.BOARD_EDGE,sash.CASE] if int(l)==2 and int(a)>3 else shade+[sash.STEEL,sash.BEAD,sash.CASE]
    named_obs = data('nanxun-named-and-two-street-marks.json')
    for key,pts in named_obs['native_mouths'].items():
        photo_ray(key,pts,'named66',expected(key))
    for r in data('independent-street-sash-heights.json')['rows']:
        if r['station'] not in ('last-5-256','last-2-216'):
            continue
        pts={p['point']:p['uv']for p in r['points']}
        photo_ray(r['id'],pts,r['station']+'-named-control',expected(r['id']))
    def counts(rows):
        return dict(total=len(rows),matched=sum(v['matched'] for v in rows))
    return dict(glb_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), geometric=counts(structure),
                initial_photo_controls=counts(photo[:before]), additional_photo_controls=counts(photo[before:]), source_photo=counts(photo), per_photo={k:counts([p for p in photo if p['camera']==k]) for k in cameras},
                first_surfaces_only=True, geometry_rays=structure, image_rays=photo)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    report=inspect(args.asset)
    raw=(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(gzip.compress(raw,mtime=0) if args.output.suffix=='.gz' else raw)
    print(report['glb_sha256'],report['geometric'],report['per_photo'])
