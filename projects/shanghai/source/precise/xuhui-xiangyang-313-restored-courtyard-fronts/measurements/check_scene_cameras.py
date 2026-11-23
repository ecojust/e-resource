"""Check the embedded nine camera records against the 3304 transform and visible window framing."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import numpy as np
from make_cameras import make

HERE=Path(__file__).resolve().parent

def project(view,points):
    eye=np.asarray(view['eye'])
    forward=np.asarray(view['target'])-eye
    distance=np.linalg.norm(forward)
    forward/=distance
    side=np.cross(forward,[0.,0.,1.])
    side/=np.linalg.norm(side)
    up=np.cross(side,forward)
    displacement=points-eye
    depth=displacement@forward
    if np.any(depth<=0):
        raise ValueError('Target geometry crosses the camera')
    focal=view['width']*distance/view['width_m']
    return np.column_stack((view['width']/2+focal*(displacement@side)/depth,
                            view['height']/2-focal*(displacement@up)/depth))

def extent(view,xyz):
    points=project(view,xyz)
    bounds=[points.min(0),points.max(0)]
    assert np.all(bounds[0]>0) and np.all(bounds[1]<[view['width'],view['height']])
    return [x.tolist() for x in bounds]

def run(mesh,parts):
    payload=mesh.read_bytes()
    n=struct.unpack_from('<I',payload,12)[0]
    doc=json.loads(payload[20:20+n])
    camera_file=HERE.parent/'source/cameras.json'
    generated=(json.dumps(make(),ensure_ascii=False,indent=2)+'\n').encode()
    assert generated==camera_file.read_bytes()
    embedded=doc['extras']['camera_views']
    assert embedded==json.loads(generated)
    views={v['name']:v for v in embedded}
    pieces=json.loads(parts.read_bytes())['groups']
    all_xyz=np.concatenate([np.array(g['v']) for g in pieces.values()])
    rail=next(np.array(g['v']) for k,g in pieces.items() if k.endswith('large window/outer frame'))
    window=extent(views['twenty-lights'],rail)
    center=(np.asarray(window[0])+window[1])/2
    v=views['twenty-lights']
    assert np.linalg.norm((center-[v['width']/2,v['height']/2])/[v['width'],v['height']])<.1
    return dict(source_raw_sha256=hashlib.sha256(payload).hexdigest(),
                camera_file_sha256=hashlib.sha256(generated).hexdigest(),
                plan_sha256=hashlib.sha256((HERE/'3304-local-footprint.json').read_bytes()).hexdigest(),
                regenerated_from_current_plan=len(views),overview_px=extent(views['overview'],all_xyz),
                window_px=window,window_center_px=center.tolist(),photo_views=[v['reference'] for v in embedded if 'reference' in v])
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('raw_glb','editable_parts','report'):
        parser.add_argument(name,type=Path)
    args=parser.parse_args()
    report=run(args.raw_glb,args.editable_parts)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
