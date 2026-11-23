"""Check all nine camera frames and visibility using the serialized triangles."""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from check_entrance import PROBES, SerialScene
from check_lane_return import M as SIDE_MATERIALS
from register_street import Camera

HERE=Path(__file__).resolve().parent


def normalized(v):
    return v/np.linalg.norm(v)


def view_matrix(v):
    eye=np.array(v['eye']);forward=normalized(np.array(v['target'])-eye)
    right=normalized(np.cross(forward,v.get('world_up',[0,0,1.])))
    up=np.cross(right,forward);axes=np.array([right,-up,forward])
    w,h=v['width'],v['height']
    f=w*np.linalg.norm(eye-v['target'])/v['width_m']
    k=np.array([[f,0,(w-1)/2],[0,f*v.get('pixel_aspect_y',1),(h-1)/2],[0,0,1]])
    return k@np.column_stack([axes,-axes@eye])


def project(matrix,xyz):
    xyz=np.atleast_2d(xyz);p=xyz@matrix[:,:3].T+matrix[:,3]
    return p[:,:2]/p[:,2,None]


def check(mesh,cameras):
    scene=SerialScene(mesh)
    presets=json.loads(cameras.read_bytes());views={r['name']:r for r in presets}
    visible={}
    for v in presets:
        name=v['name'];p=view_matrix(v);w,h=v['width'],v['height']
        alluv=project(p,scene.tri.reshape(-1,3));bounds=[*alluv.min(axis=0),*alluv.max(axis=0)]
        report={'dimensions':[w,h],'actual_vertex_bbox_px':np.round(bounds,3).tolist(),
                'all_vertex_clearances_ltrb_px':np.round([bounds[0]+.5,bounds[1]+.5,w-.5-bounds[2],h-.5-bounds[3]],3).tolist(),
                'subjects':[]}
        if 'reference' in v:
            source=Camera(v['reference'])
            truth=project(source.P,scene.tri.reshape(-1,3))
            report['reference_max_vertex_projection_error_px']=float(np.max(np.abs(truth-alluv)))
        visible[name]=report
    full=Camera('2018')
    def test(name,feature,station,pixel,expected):
        origin=Camera(station);v=views[name];eye=np.array(v['eye'])
        real=scene.ray(origin.c,origin.ray(pixel),60)
        r={'feature':feature,'registered_station':station,'source_pixel':pixel,'expected':expected,'source_hit':real}
        if real:
            target=np.array(real['point_enu_m']);uv=project(view_matrix(v),target)[0]
            ray=scene.ray(eye,target-eye,60)
            dist=np.linalg.norm(target-np.array(ray['point_enu_m'])) if ray else None
            r.update(frame_px=np.round(uv,3).tolist(),inside=bool(0<=uv[0]<v['width'] and 0<=uv[1]<v['height']),
                     first_hit=ray,surface_offset_m=dist,visible=bool(ray and ray['material'] in expected and real['material'] in expected and dist<.08))
        visible[name]['subjects'].append(r)
    rows=json.loads((HERE/'front-window-photo-points.json').read_bytes())['windows']
    glass=['Xinlefang | '+n+' steel window glass' for n in ['sky-lit','shaded']]
    for row in rows:
        corners=project(view_matrix(views['staggered-windows']),[full.wall(p,0)for p in row['aperture_2018_original_px']])
        visible['staggered-windows'].setdefault('entire_aperture_frames',{})[row['name']]=np.round(corners,2).tolist()
        test('staggered-windows',row['name'],'2018',row['glass_control_2018_px'][0],glass)
    for p in rows[2]['glass_control_2018_px']:test('upper-sashes',rows[2]['name'],'2018',p,glass)
    for n in ['black door plate background','green lane plate background','silver ends of service fittings']:
        m,pts=PROBES[n];name='service-pipes' if n.startswith('silver')else'two-numbers'
        for p in pts:test(name,n,'2018',list(p),['Xinlefang | '+m])
    sides=json.loads((HERE/'lane-return-ray-pixels.json').read_bytes())
    for e in sides['1512-4']['samples']:
        test('lane-return',e['feature'],'1512-4',e['pixel'],['Xinlefang | '+SIDE_MATERIALS[m] for m in e['expected_part']])
    roof=json.loads((HERE/'roof-edge-photo-controls.json').read_bytes())
    for e in roof['held_out_native'][:9]:test('roof-eaves',e['feature'],'2018',e['native_uv'],[roof['surfaces'][e['surface']]])
    return {'asset':scene.asset,'camera_file_sha256':hashlib.sha256(cameras.read_bytes()).hexdigest(),'cameras':visible}


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    cli.add_argument('--cameras',type=Path,default=HERE.parent/'source/cameras.json');args=cli.parse_args()
    report=check(args.mesh,args.cameras);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    for k,v in report['cameras'].items():
        a=v['subjects'];print(k,v['all_vertex_clearances_ltrb_px'] if k=='overview' else '',
              len(a),sum(bool(x.get('inside')and x.get('visible')) for x in a),v.get('reference_max_vertex_projection_error_px',''))
