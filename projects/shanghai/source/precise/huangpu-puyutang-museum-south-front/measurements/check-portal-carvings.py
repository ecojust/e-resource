"""Check the date, exposed surround, ribbon and small fruit hollows against the portal photograph."""
import argparse
import json
from pathlib import Path
import runpy
import sys

import numpy as np


def check(project,source,mesh,isolated):
    sys.path.insert(0,str(source))
    from photo_plane import position,CAMERAS
    from portal_carvings import STONE,LETTERS
    lib=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    triangles,ids,names,identity=lib['load_triangles'](mesh)
    props=lib['material_appearance'](mesh)['materials']
    double=np.array([props[n]['doubleSided']for n in names])[ids]
    normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    vertex=triangles.reshape(-1,3)
    uvw=np.column_stack((vertex,np.ones(len(vertex))))@CAMERAS['close'].T
    uv=(uvw[:,:2]/uvw[:,2,None]).reshape(-1,3,2)
    lo,hi=uv.min(axis=1)-.001,uv.max(axis=1)+.001
    def shoot(p):
        p=np.asarray(p,float)
        a=position(*p,-2.);d=position(*p,1.)-a;d/=np.linalg.norm(d)
        valid=(double|((normals@d)<-1e-12))&np.all(lo<=p,axis=1)&np.all(hi>=p,axis=1)
        index=np.flatnonzero(valid)
        if len(index):
            i,t,xyz=lib['first_hit'](triangles[index],a,d)
            if np.isfinite(t):return names[ids[index[i]]],round(float(xyz[1]),7)
        return None,None
    num=[[39.5,36.],[40.,43.],[41.,49.5],[37.7,50.1],
         [57.,39.],[65.1,42.],[65.,47.2],[60.5,52.5],
         [83.2,37.1],[87.9,41.4],[84.5,48.],[82.5,53.9],
         [109.3,39.6],[107.,43.3],[113.7,47.],[109.,55.8]]
    holes=[[60.2,40.1],[61.,42.],[50.,42.],[71.,47.],[98.,46.],[120.5,46.],[37.,55.5]]
    folds=[[51.,31.],[31.5,44.1],[59.,51.],[80.,33.],[83.2,53.4],[119.,42.],
           [119.7,68.2],[144.,47.6],[164.,63.2],[41.,75.],[155.,95.]]
    clear=[[61.,38.],[78.8,38.2],[114.5,47.8],[143.,62.],[124.5,71.5],[54.,83.]]
    points=[]
    for role,offset,locations in [('date face',[318,575],num),('date backing',[318,575],holes),
                                  ('stone fold',[288,233],folds),('swag backing',[288,233],clear)]:
        for q in locations:
            p=np.add(q,offset);material,y=shoot(p)
            if role in ('date face','stone fold'):
                good=material==(LETTERS if role=='date face' else STONE)
            else:
                good=material is None if isolated else material not in {None,LETTERS,STONE} and abs(y+.24)<.025
            points.append({'feature':role,'source_px':p.tolist(),'material':material,'model_y':y,'passed':good})
    hollows=[]
    for q in [[83.,74.],[88.,74.1],[97.9,83.],[113.9,86.]]:
        p=np.add(q,[288,233]);material,y=shoot(p);rim=[]
        for a in np.arange(12)*np.pi/6:
            m,d=shoot(p+1.55*np.array([np.cos(a),np.sin(a)]))
            if m==STONE:rim.append(d)
        depth=round(y-float(np.percentile(rim,35)),6) if y is not None and len(rim)>=9 else None
        hollows.append({'source_px':p.tolist(),'rim_samples':len(rim),'rim_relief_m':depth,'passed':material==STONE and depth is not None and depth>.003})
    return dict(mesh=identity,points=points,hollows=hollows)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('project','source','mesh','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--isolated',action='store_true')
    a=p.parse_args();r=check(a.project,a.source,a.mesh,a.isolated)
    a.output.write_text(json.dumps(r,ensure_ascii=False,indent=1)+'\n')
    fail=[s for s in r['points'] if not s['passed']]
    print(len(r['points'])-len(fail),len(r['points']),[(s['feature'],s['source_px'],s['material'])for s in fail],r['hollows'])
    if fail or not all(s['passed']for s in r['hollows']):raise SystemExit(1)
