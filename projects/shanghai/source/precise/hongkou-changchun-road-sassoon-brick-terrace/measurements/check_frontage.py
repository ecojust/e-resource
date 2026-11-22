"""Check the first surface at independently marked pixels of the north elevation."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene

def check(path):
    scene=SerialScene(path)
    cam_file=HERE/'north-frontage-cameras.json';points_file=HERE/'north-frontage-sightlines.json'
    p=np.array(json.loads(cam_file.read_bytes())['front']);d=json.loads(points_file.read_bytes())
    eye=np.linalg.solve(p[:,:3],-p[:,3]);rows=[]
    for kind,points in d['pixels'].items():
        for uv in points:
            ray=np.linalg.solve(p[:,:3],[*uv,1.]);first=scene.ray(eye,ray,90.)
            mat=first['material'] if first else None
            rows.append(dict(group=kind,uv=uv,expected=d['groups'][kind],first_material=mat,first_xyz=first['point_enu_m'] if first else None,passed=mat in d['groups'][kind]))
    hits=sum(q['passed']for q in rows)
    return dict(mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),mesh_bytes=path.stat().st_size,tests=rows,hits=hits,total=len(rows),passed=hits==len(rows),
                camera_sha256=hashlib.sha256(cam_file.read_bytes()).hexdigest(),points_sha256=hashlib.sha256(points_file.read_bytes()).hexdigest())
