"""Check the first surface at independently marked pixels of the two photographs of Gongyuanfang No. 24."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene

def check(path):
    scene=SerialScene(path)
    cam_file=HERE/'two-cameras-and-curved-sill.json';points_file=HERE/'two-photo-surface-targets.json'
    cameras=json.loads(cam_file.read_bytes());press=HERE/'press-entrance-camera.json';cameras['press']=json.loads(press.read_bytes())['press'];d=json.loads(points_file.read_bytes());rows=[]
    for view,observations in d['pixels'].items():
        p=np.asarray(cameras[view]);eye=np.linalg.solve(p[:,:3],-p[:,3])
        for kind,points in observations.items():
            for uv in points:
                ray=np.linalg.solve(p[:,:3],[*uv,1.]);first=scene.ray(eye,ray,90.)
                mat=first['material'] if first else None
                rows.append(dict(view=view,group=kind,uv=uv,expected=d['groups'][kind],first_material=mat,first_xyz=first['point_enu_m'] if first else None,passed=mat in d['groups'][kind]))
    hits=sum(q['passed']for q in rows)
    return dict(mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),mesh_bytes=path.stat().st_size,tests=rows,hits=hits,total=len(rows),passed=hits==len(rows),
                camera_sha256=hashlib.sha256(cam_file.read_bytes()).hexdigest(),press_camera_sha256=hashlib.sha256(press.read_bytes()).hexdigest(),points_sha256=hashlib.sha256(points_file.read_bytes()).hexdigest())
