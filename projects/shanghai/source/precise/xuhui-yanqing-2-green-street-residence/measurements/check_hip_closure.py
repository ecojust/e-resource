"""Trace the overview screen pixels in the east hip opening recorded during the first roof review."""
from pathlib import Path
import sys,json,argparse,hashlib
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
def inspect(mesh):
    camera=next(c for c in json.loads((HERE.parent/'source/cameras.json').read_text()) if c['name']=='overview')
    eye=np.array(camera['eye']);f=np.array(camera['target'])-eye;dist=np.linalg.norm(f);f/=dist
    right=np.cross(f,[0,0,1.]);right/=np.linalg.norm(right);down=np.cross(f,right);focal=600*dist/camera['width_m'];scene=SerialScene(mesh)
    pixels=json.loads((HERE/'overview-hip-screen-pixels.json').read_bytes())
    rows=[]
    for x,y in pixels['pixels']:
        direction=f+right*(x+.5-300)/focal+down*(y+.5-204)/focal
        hit=scene.ray(eye,direction,90);rows.append(dict(pixel=[x,y],actual=hit))
    return {'mesh':mesh.name,'sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),'checks':len(rows),'hits':sum(bool(r['actual']) for r in rows),'rows':rows}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('report',type=Path);a=p.parse_args();r=inspect(a.mesh);a.report.write_text(json.dumps(r,indent=2)+'\n');print(r['hits'],r['checks'])
