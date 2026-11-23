"""Intersect manually selected native photo pixels with an actual author or decoded release GLB."""
from pathlib import Path
import argparse,json,hashlib,runpy
import numpy as np
HERE=Path(__file__).absolute().parent
GROUP={'roughcast':['coarse grey-brown pebble dash'],'brick':['warm red facing brick'],'tile':['terracotta roof'],'window':['green-grey glazing','weathered green joinery','pale gallery frames'],'coping':['warm grey coping'],'door':['weathered green joinery']}
def evaluate(mesh):
    H=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
    scene=runpy.run_path(str(H))['SerialScene'](mesh);cams=json.loads((HERE/'three-tower-stations.json').read_bytes())['stations'];points=json.loads((HERE/'tower-surface-controls.json').read_bytes());out={}
    for key,obs in points.items():
        cam=cams[key];eye=np.array(cam['C']);inv=np.array(cam['R']).T@np.linalg.inv(cam['K']);records=[]
        limit=3 if key=='numbered-court'else 7
        shifts=sorted([(i,j)for i in range(-limit,limit+1)for j in range(-limit,limit+1)if i*i+j*j<=limit**2],key=lambda x:x[0]**2+x[1]**2)
        for label,u,v,expect in obs:
            first=None;match=None
            for dx,dy in shifts:
                hit=scene.ray(eye,inv@[u+dx,v+dy,1.],140)
                if dx==dy==0:first=hit
                if hit and any(hit['material'].endswith(m) for m in GROUP[expect]):match=[dx,dy];break
            records.append(dict(label=label,native_pixel=[u,v],expected=expect,first_hit=first,nearest_in_radius_px=match))
        out[key]=dict(total=len(records),direct=sum(q['nearest_in_radius_px']==[0,0]for q in records),within_radius=sum(q['nearest_in_radius_px'] is not None for q in records),radius=limit,points=records)
    return dict(mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),stations=out)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=evaluate(a.mesh);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({k:(v['direct'],v['within_radius'],v['total'])for k,v in r['stations'].items()})
