"""Cast rays through identifiable features from each ordinary-page camera."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'source'
sys.path[:0] = [str(SOURCE),str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from glb_triangles import SerialScene
from build_model import SCALE
import loggia_materials as center
import wing_openings as wing

def features():
    walls=json.loads((SOURCE/'wing_layout.json').read_bytes())['wings']
    tests={
        'overview':[('central street wall',(-3.75,0,7.60),center.ROUGHCAST),('upper landing door',(-1.25,2.32,8.35),center.GREEN)],
        'loggia':[('lower landing door',(-1.28,2.32,4.18),center.GREEN),('high recessed glazing',(1.55,2.34,9.45),center.GLASS),('left arch shoulder',(-2.7,0,9.85),center.ROUGHCAST)],
        'steps':[('top face of first exposed tread',(.02,1.35,6.70),center.CEMENT),('upper-flight handrail',(.71,.10,7.36-1.38*(.71+.075)/2.085+.94),center.STEEL),('lower platform',(2.50,1.35,5.29),center.CEMENT)],
        'arch':[('rear green door',(-1.31,2.32,8.32),center.GREEN),('recessed upper glass',(1.55,2.34,9.49),center.GLASS),('arch shoulder',(-2.65,0,9.86),center.ROUGHCAST)],
        'vents':[('middle ventilator cross',(.30,.011,12.04),center.STEEL),('left small vent',(-.33,.011,12.01),center.STEEL),('right vent rim',(1.041,-.003,12.04),center.LIME)],
        'eaves':[('right-hand return side',(7.30322,3.50,10.64),center.ROUGHCAST),('central lime front',(.70,0,12.92),center.ROUGHCAST)]
    }
    right=walls['right']['x1']
    tests['south-roof']=[
        ('high casement between the eave and the first bay',(right-.118,6.70,9.52),wing.GLASS),
        ('shallow projecting bay glass',(right+3.05/SCALE-.118,6.78,4.54),wing.GLASS),
        ('deep projecting bay glass',(right+3.77/SCALE-.118,11.08,4.63),wing.GLASS)]
    for label,y,z in [('lower left',16.915,13.01),('upper',17.435,13.56),('lower right',17.955,13.01)]:
        tests['south-roof'].append((label+' chimney diamond recess',(right-.09-.72,y,z),center.SHADE))
    for name,key in [('left-fan','left'),('right-fan','right')]:
        panel=walls[key]
        a,low,b,high=panel['windows']['upper fan']['bounds']
        y=panel['y'];scale=panel['angular_scale']
        width=b-a;x=(a+b)/2
        tests[name]=[('fanlight outer glass sector',(x+.14*width,y+.118*scale,high-.15*width),wing.GLASS),
                     ('main sash glazing',(a+.24*width,y+.118*scale,low+.21*(high-low)),wing.GLASS),
                     ('projecting cement sill',(x,y-.035*scale,low-.024*scale),wing.SILL)]
    return tests

def project(camera,point):
    eye=np.array(camera['eye']);forward=np.array(camera['target'])-eye;distance=np.linalg.norm(forward);forward/=distance
    right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(forward,right)
    delta=point-eye;depth=np.dot(delta,forward)
    fx=distance*camera['width']/camera['width_m']
    return [float(.5+fx*np.dot(delta,right)/(depth*camera['width'])),float(.5+fx*np.dot(delta,down)/(depth*camera['height']))]

def inspect(mesh,camera_file):
    cams=json.loads(camera_file.read_bytes());tests=features();assert set(tests)=={c['name'] for c in cams}
    scene=SerialScene(mesh);rows=[]
    for camera in cams:
        eye=np.array(camera['eye'])
        for feature,local,expected in tests[camera['name']]:
            target=np.array(local)*SCALE
            uv=project(camera,target);hit=scene.ray(eye,target-eye,140)
            inside=all(0<v<1 for v in uv)
            rows.append(dict(camera=camera['name'],feature=feature,expected=expected,target_m=target.tolist(),
                             relative_image_position=uv,first_hit=hit,within_frame=inside,
                             matches=bool(inside and hit and hit['material']==expected)))
    return dict(mesh=mesh.name,mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),
                cameras_sha256=hashlib.sha256(camera_file.read_bytes()).hexdigest(),count=len(rows),
                matched=sum(r['matches'] for r in rows),observations=rows)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--cameras',type=Path,default=SOURCE/'cameras.json');a=p.parse_args()
    r=inspect(a.mesh,a.cameras);a.output.write_text(json.dumps(r,indent=2)+'\n')
    for x in r['observations']:
        if not x['matches']:print(x['camera'],x['feature'],x['first_hit'] and x['first_hit']['material'],x['relative_image_position'])
    print(r['matched'],'/',r['count'])
