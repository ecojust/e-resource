"""Intersect exported triangles at the street façade's recorded apertures, masonry and cornices."""
import json, runpy, sys
from pathlib import Path
from shapely.geometry import Polygon
import numpy as np
AUDIT=Path(__file__).absolute().parent
PROJECT=next(d for d in AUDIT.parents if (d/'tools/package_architectural_model.py').is_file())
SOURCE=PROJECT/'source/precise/huangpu-shanghai-tramways-suzhou-road-front'
sys.path.insert(0,str(SOURCE/'source'))
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from frontage import DOOR,CREAM,RED,KEY,TIMBER,GLASS,DARK,IRON,SHADOW
from material_names import MATERIAL
inspect=runpy.run_path(str(PROJECT/'data/audit/central-reserve-bank-changshu-front-v1/verify-export.py'))['inspect']
def cases():
    rows=json.loads((SOURCE/'measurements/facade-apertures.json').read_text())['openings']
    tests=[]
    def ray(name,x,z,y,materials,tol=.009):
        tests.append(dict(name=name,origin=[x,-1.5,z],direction=[0,1,0],length=2.5,allowed=materials,range_m=[1.5+y-tol,1.5+y+tol]))
    for row in rows:
        x0,z0,x1,z1=Polygon(row['rectified_xz_m']).bounds;w=x1-x0;h=z1-z0
        tier=row['tier']; col=row['column']; label=f'{tier} window {col}'
        # The balcony projects in front of the upper-centre opening.
        if tier!='upper' or col not in [3,4,5]:
            ray(label+' pane',x0+.294*w,z0+h*.42,.292,[DARK if tier=='street' else GLASS])
            ray(label+' jamb stile',x0+.025,z0+.47*h,.230,[TIMBER])
        if tier in ['lower','middle','street'] and (tier!='middle' or col not in [3,4]):
            ray(label+' protruding central lintel key',(x0+x1)/2,z1+.27,-.135,[KEY])
        if tier in ['lower','middle','upper'] and (tier!='upper' or col not in [3,4,5]):
            ray(label+' projected sill',(x0+x1)/2,z0-.035,-.194,[RED])
    for i,(x,z,y,mat) in enumerate([(-7.2,20.2,0,MATERIAL),(-7.,9.29,0,MATERIAL),(-7.0,4.04,-.038,MATERIAL),
                                     (-1.5,5.30,-.30,CREAM),(4.0,17.30,-.47,SHADOW),
                                     (-5.5,21.40,-.49,RED),(0.,16.99,-.16,SHADOW)]):
        ray('street wall and entablature '+str(i+1),x,z,y,[mat])
    # Sightlines through the visible left-hand slit in the previous entrance
    # photograph-style preview. Use the same registered perspective camera.
    cam=next(q for q in json.loads((SOURCE/'source/cameras.json').read_bytes())if q['name']=='entrance')
    eye=np.array(cam['eye']);delta=np.array(cam['target'])-eye;length=np.linalg.norm(delta)
    forward=delta/length;right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    focal=length*cam['width']/cam['width_m']
    for row in (280,311,342,373,404,435,466):
        for col in (277,279,281):
            sight=forward+(col+.5-cam['width']/2)*right/focal-(row+.5-cam['height']/2)*up/focal
            sight/=np.linalg.norm(sight)
            tests.append(dict(name=f'entrance masonry return at preview pixel {col} {row}',origin=eye.tolist(),direction=sight.tolist(),
                              length=15.,allowed=[SHADOW,DOOR,MATERIAL,DARK],range_m=[8.5,12.5]))
    return tests
if __name__=='__main__':
    files=list(map(Path,sys.argv[1:]))
    roles=['raw','full','lod'] if len(files)==4 else ['model']
    probes=cases();results={role:inspect(f,probes) for role,f in zip(roles,files[:-1])}
    files[-1].write_text(json.dumps(results,ensure_ascii=False,indent=1)+'\n')
    failed={k:[(t['name'],t.get('first_hit'))for t in r['cases']if not t['passed']]for k,r in results.items()}
    print(len(probes),failed,flush=True);sys.exit(int(any(failed.values())))
