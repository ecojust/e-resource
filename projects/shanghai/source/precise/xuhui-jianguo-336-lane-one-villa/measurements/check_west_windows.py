"""Trace the first visible surface at measured photograph pixels on the real exported GLB."""
from pathlib import Path
import argparse,hashlib,json,runpy,sys
import numpy as np
from register_court import Camera
HERE=Path(__file__).absolute().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'hongkou-general-post-office/source/common')]
from west_side import SLAT,CORD,VOID,PIPE,STONE,CARVED,RECESS
def sh(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def load(n):return json.loads((HERE/n).read_bytes())
def samples():
    data=load('west-wall-photo-controls.json')
    out=[]
    for name,row in data['windows'].items():
        xy=np.array(row['original_image_corners_px'])
        for label,t in [('upper blades',.34),('lower blades',.63)]:
            out.append(('04',name+' / '+label,((1-t)*(.57*xy[0]+.43*xy[1])+t*(.57*xy[3]+.43*xy[2])).tolist(),[SLAT,CORD,VOID]))
    for k in ('south-pipe-belt','south-pipe-belt-low','north-pipe-ring','north-pipe-foot-visible','near-wall-seam-mid'):
        out.append(('04',k,data['other_controls'][k]['source_px'],[STONE] if k.startswith('near-wall') else [PIPE]))
    for k in ('upper-carving-south-southwest-stem','upper-carving-north-stem'):
        out.append(('04',k,data['other_controls'][k]['source_px'],[CARVED,RECESS]))
    # Interior traces from 02 are separate from its 20 registration corner points.
    for name,uv in [('near high dark blind',[165,179]),('near middle dark blind',[163,330]),('further upper dark blind',[83,250]),('further middle dark blind',[77,359]),('rear visible upper dark blind',[30,307])]:
        out.append(('02',name,uv,[SLAT,CORD,VOID]))
    for name,uv in [('first shaft',[237,223]),('first lower shaft',[237,260]),('rear shaft',[59,303])]:out.append(('02',name,uv,[PIPE]))
    out.extend([('02','plain pale block between windows',[203,245],[STONE]),('02','rectangular sprig field below nearer blind',[162,251],[RECESS,CARVED,STONE])])
    return out
def inspect(path):
    scene=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'](path)
    c4=Camera('04');p=load('west-photo02-camera.json');c2=np.array(p['C']);inv2=np.asarray(p['R']).T@np.linalg.inv(p['K'])
    result=[]
    for station,name,px,expected in samples():
        c=c4.c if station=='04' else c2
        direction=(lambda q:c4.ray(q)) if station=='04' else (lambda q:inv2@np.r_[q,1.])
        exact=scene.ray(c,direction(px),80)
        radius=8 if station=='04' else 5
        first=None
        for d,u,v in sorted((u*u+v*v,u,v)for u in range(-radius,radius+1) for v in range(-radius,radius+1) if u*u+v*v<=radius*radius):
            hit=exact if d==0 else scene.ray(c,direction(np.array(px)+[u,v]),80)
            if hit and hit['material'] in expected:first=dict(offset_px=[u,v],distance_px=float(np.sqrt(d)),hit=hit);break
        result.append(dict(station=station,name=name,source_pixel=px,expected=expected,first_hit=exact,nearest=first))
    return dict(file=path.name,file_sha256=sh(path),camera_sha256={n:sh(HERE/n)for n in ['court-cameras.json','west-photo02-camera.json']},rays=result,exact=sum(bool(r['nearest'] and r['nearest']['distance_px']==0)for r in result),within_radius=sum(bool(r['nearest'])for r in result),total=len(result))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('glb',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=inspect(a.glb);a.out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
    print(r['exact'],r['within_radius'],r['total'])
    for row in r['rays']:
        if not row['nearest']:print(row['station'],row['name'],str(row['first_hit'])[:135])
