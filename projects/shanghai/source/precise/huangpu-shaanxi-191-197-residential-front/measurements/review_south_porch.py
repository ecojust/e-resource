"""Project the actual 2018 front-porch details into a delivered glTF and inspect first hits."""
import argparse
import json
from pathlib import Path
import runpy
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"source"))
from west_photo_plane import matrix
from south_loggia import RIM,IRON,BRICK,MORTAR,GLASS,METAL,SHELTER,INSIDE

def check(mesh):
    helpers=runpy.run_path(HERE.parents[3]/"data/audit/postal-office-v1/independent-glb-review-helpers.py")
    tri,mi,names,asset=helpers['load_triangles'](mesh)
    camera=matrix();inverse=np.linalg.inv(camera[:,:3]);eye=-inverse@camera[:,3]
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);uv=tri.reshape(-1,3)@camera[:,:3].T+camera[:,3]
    pp=(uv[:,:2]/uv[:,2,None]).reshape(-1,3,2);mn=pp.min(1);mx=pp.max(1);tiles={}
    def hit(pt):
        xy=np.array(pt);key=tuple(np.floor(xy/32).astype(int))
        if key not in tiles:
            lo=np.array(key)*32.;tiles[key]=np.flatnonzero((mn<=lo+32.).all(1)&(mx>=lo).all(1))
        ray=inverse@np.r_[xy,1.];ray/=np.linalg.norm(ray)
        ii=tiles[key];ii=ii[(mn[ii]<=xy+.00001).all(1)&(mx[ii]>=xy-.00001).all(1)&(normal[ii]@ray<0)]
        if not len(ii):return None
        k,d,_=helpers['first_hit'](tri[ii],eye,ray)
        return names[mi[ii[k]]] if np.isfinite(d) else None
    trace=json.loads((HERE/'south-porch-arch-trace.json').read_bytes())
    tips=json.loads((HERE/'south-porch-toothed-jambs.json').read_bytes())
    parts=json.loads((HERE/'south-porch-fittings.json').read_bytes());probes=[]
    def record(key,point,matches):
        surface=hit(point);probes.append({'detail':key,'native_px':np.round(point,3).tolist(),
            'first_surface':surface,'expected':matches,'passed':surface in matches})
    for i,r in enumerate(trace['samples']):
        p=(np.array(r['inner_px'])+r['outer_px'])/2
        record('Smooth arch rim '+str(i+1),p,[RIM])
    for group in tips['jambs']:
        for k,r in enumerate(group['courses']):
            if not r['tooth_tip'].startswith('visible'):continue
            y=(r['top_native_v']+r['bottom_native_v'])/2
            record(group['level']+' exposed red end '+str(k+1),[r['left_native_u']+5,y],[*BRICK,MORTAR])
    for k,u in enumerate(parts['front_rail']['uprights_at_native_v_1300']):
        record('Upper front iron upright '+str(k+1),[u,1300],[IRON])
    for u,v,mat,desc in [(2753,1021,GLASS,'Upper pendant bowl'),(2753,1009,METAL,'Upper dark cap'),
                         (2760,1635,GLASS,'Ground pendant bowl'),(2760,1623,METAL,'Ground dark cap')]:
        record(desc,[u,v],[mat])
    sides=json.loads((HERE/'south-porch-side-witnesses.json').read_bytes())
    for i,w in enumerate(sides['pairs']):
        for tag,expected in [('darker_shaded_face_px',SHELTER),('lighter_intrados_px',INSIDE)]:
            observation=w.get(tag.removesuffix('_px')+'_observation')
            if tag=='darker_shaded_face_px' and observation and 'metal cap' in observation:
                expected=METAL
            record(w['shoulder']+' side arch '+tag+' '+str(i+1),w[tag],[expected])
            if observation:probes[-1]['photograph_observation']=observation
    return {'mesh':asset,'primary':'2018 WQL street photograph, 4160 by 3120','tests':probes,
            'passed':sum(p['passed']for p in probes),'total':len(probes)}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();r=check(a.mesh);a.output.write_text(json.dumps(r,indent=1,ensure_ascii=False)+'\n')
    print(r['passed'],'/',r['total'],[(p['detail'],p['first_surface'])for p in r['tests']if not p['passed']])
