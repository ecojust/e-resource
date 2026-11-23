"""Test first intersections at observed 2015 glass, hardware and threshold pixels."""
from pathlib import Path
import argparse,hashlib,json,runpy
from register_porch import PorchFrame
import numpy as np

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'data/audit/postal-office-v1/independent-glb-review-helpers.py').is_file())
Scene=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']

def verify(path):
    f=PorchFrame()
    scene=Scene(path)
    controls=json.loads((HERE/'porch-doors-observations.json').read_bytes())
    rows=[]
    for c in controls['claims']:
        for point in c['pixels']:
            pixel=np.array(point)
            hit=scene.ray(f.camera.c,f.camera.ray(pixel),65)
            expected='325 garden | '+c['expected']
            error=None
            for radius in [0,.5,1,2,3]:
                for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(.707,.707),(.707,-.707),(-.707,.707),(-.707,-.707)]:
                    p=pixel+radius*np.array([dx,dy])
                    h=scene.ray(f.camera.c,f.camera.ray(p),65)
                    if h and h['material']==expected:
                        error=radius
                        break
                if error is not None:break
            rows.append({'feature':c['name'],'pixel':point,'expected':expected,
                         'first_hit':hit,'exact':error==0,'nearest_offset_px':error})
    levels={}
    for y in [.9,1.2,1.5]:
        left,center,right=[f.plane((u,906.8),y)for u in [655.,742.,829.]]
        head=f.plane((742.,681.6),y)
        levels[str(y)]={'left_span_m':float(center[0]-left[0]),'right_span_m':float(right[0]-center[0]),
                        'meeting_foot_z_m':float(center[1]),'meeting_head_z_m':float(head[1])}
    return {'photo_sha256':controls['source_images'][0]['sha256'],'glb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'triangles':len(scene.tri),'rays':len(rows),'exact_first_hits':sum(r['exact']for r in rows),
            'within_two_pixels':sum(r['nearest_offset_px'] is not None and r['nearest_offset_px']<=2 for r in rows),
            'depth_sensitivity':levels,'results':rows}
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('glb',type=Path);a.add_argument('report',type=Path)
    args=a.parse_args();r=verify(args.glb);args.report.write_text(json.dumps(r,indent=2)+'\n')
    print(r['rays'],r['exact_first_hits'],r['within_two_pixels'])
