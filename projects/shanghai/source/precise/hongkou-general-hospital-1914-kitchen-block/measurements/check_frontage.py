"""First-surface checks at independently marked pixels of the published street and courtyard photographs."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene
def check(path):
    scene=SerialScene(path);source=HERE/'photographic-surface-pixels.json';data=json.loads(source.read_bytes())
    sys.path.insert(0,str(HERE/'camera-fit'));import registered,court_registered
    cameras={'street':registered,'courtyard':court_registered};rows=[];groups={}
    for name,c in cameras.items():
        for family,points in data[name].items():
            for u,v in points:
                direction=c.R.T@np.linalg.solve(c.K,[u,v,1]);hit=scene.ray(c.eye,direction,160.)
                name_mat=hit['material'] if hit else None
                match=bool(name_mat and any(k in name_mat for k in data['material_families'][family]))
                rows.append(dict(view=name,kind=family,pixel=[u,v],material=name_mat,world_hit=hit['point_enu_m']if hit else None,passed=match))
        r=[x for x in rows if x['view']==name];groups[name]=dict(matched=sum(v['passed']for v in r),total=len(r))
    hits=sum(r['passed']for r in rows)
    return dict(mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),views=groups,hits=hits,total=len(rows),passed=all(v['matched']>=.85*v['total']for v in groups.values()),points=rows)
