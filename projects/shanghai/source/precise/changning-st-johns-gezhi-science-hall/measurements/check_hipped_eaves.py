"""Sample vertical sections at the exposed tile edge and its timber bearing in either eyebrow roof."""
from pathlib import Path
import argparse,hashlib,json,runpy
import numpy as np
HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'

def section(triangles,material_ids,materials,x,y):
    v=triangles[:,:,:2];a,b,c=v[:,0],v[:,1],v[:,2];d=b-a;e=c-a;p=np.array([x,y])-a;det=d[:,0]*e[:,1]-d[:,1]*e[:,0]
    real=np.abs(det)>1.e-9;safe=np.where(real,det,1.0);u=(p[:,0]*e[:,1]-p[:,1]*e[:,0])/safe;v=(d[:,0]*p[:,1]-d[:,1]*p[:,0])/safe
    ix=np.flatnonzero(real&(u>=0)&(v>=0)&(u+v<=1));z=triangles[:,0,2]+u*(triangles[:,1,2]-triangles[:,0,2])+v*(triangles[:,2,2]-triangles[:,0,2]);return [{'z':round(float(z[i]),4),'material':materials[material_ids[i]]}for i in sorted(ix,key=lambda k:z[k],reverse=True)]

def inspect(path):
    tri,mi,mats,_=runpy.run_path(str(HELPER))['load_triangles'](path);s=json.loads((HERE/'science-registration.json').read_bytes())['metres_per_reference_pixel'];rows=[]
    for u in (69,509):
        cx=(u-323)*s
        for dx in (-2.39,2.37):
            y=-.753;hits=section(tri,mi,mats,cx+dx,y);tile=[h['z']for h in hits if h['material'].endswith('dark glazed roof')];rows.append(dict(probe='free upturned corner',x=cx+dx,y=y,top_two_tile_intersections_m=tile[:2],tile_edge_m=round(tile[0]-tile[1],4)if len(tile)>1 else None))
        for dx in (-.4,.47):
            y=.11;hits=section(tri,mi,mats,cx+dx,y);rows.append(dict(probe='inboard bearing',x=cx+dx,y=y,upper_5m=[h for h in hits if h['z']>10.5],timber_bearing=any(h['material'].endswith('dark casement timber')and h['z']>12. for h in hits)))
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),sections=rows)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);a=p.parse_args();a.out.write_text(json.dumps(inspect(a.mesh),indent=2)+'\n')
