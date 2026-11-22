"""Check the first surface at independently marked pixels of the Yimin former canteen photographs."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene

def check(path):
    scene=SerialScene(path)
    front=json.loads((HERE/'two-terminal-cameras.json').read_text())['views']
    canal=json.loads((HERE/'canal-side-camera.json').read_text())
    northwest=np.asarray(front[0]['P'])
    southeast=np.asarray(front[1]['P'])@np.array([[-1,0,0,18.7],[0,-1,0,56.5],[0,0,1,0],[0,0,0,1]])
    cameras={'northwest':northwest,'southeast':southeast,'canal':np.asarray(canal['P'])}
    source=HERE/'photographic-surface-pixels.json'
    d=json.loads(source.read_text())
    rows=[]
    for view,pixels in d['pixels'].items():
        p=cameras[view];eye=np.linalg.solve(p[:,:3],-p[:,3])
        for kind,points in pixels.items():
            for uv in points:
                direction=np.linalg.solve(p[:,:3],[*uv,1])
                first=scene.ray(eye,direction,120.)
                material=first['material'] if first else None
                rows.append(dict(view=view,group=kind,uv=uv,expected=d['groups'][kind],first_material=material,first_xyz=first['point_enu_m'] if first else None,passed=material in d['groups'][kind]))
    hits=sum(r['passed'] for r in rows)
    counts={v:dict(matches=sum(r['passed'] for r in rows if r['view']==v),total=sum(r['view']==v for r in rows)) for v in cameras}
    return dict(mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),hits=hits,total=len(rows),views=counts,passed=all(c['matches']/c['total']>=.80 for c in counts.values()),observations=rows)
