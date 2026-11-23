"""Shoot first-hit rays from the two 2016 photographs at measured window details."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'source'), str(HERE.parent.parent/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from register_house import Camera
from glb_triangles import SerialScene

GLASS='280-2 | grey-green corner glass'
SHADE='280-2 | shaded inner corner glass'
STEEL='280-2 | dark steel joinery'
SILL='280-2 | weathered sill stone'
WALL='280-2 | pale ochre roughcast'
def verify(path):
    scene=SerialScene(path)
    control=json.loads((HERE/'corner-photo-controls.json').read_bytes())
    tests=[]
    for code,levels in control['original_observations'].items():
        camera=Camera(code)
        def shot(name,level,uv,expected):
            uv=list(uv)
            def hit(x,y):
                got=scene.ray(camera.c,camera.ray((x,y)),length=70)
                return got['material'] if got else None
            mat=hit(*uv); radius=None
            if mat in expected:radius=0.
            else:
                for dx,dy in sorted(((i,j) for i in range(-4,5) for j in range(-4,5) if i*i+j*j<=16 and i*i+j*j>0),key=lambda v:v[0]*v[0]+v[1]*v[1]):
                    if hit(uv[0]+dx,uv[1]+dy) in expected:
                        radius=float(np.hypot(dx,dy));break
            tests.append(dict(station=code,level=level,feature=name,source_pixel=uv,expected=expected,first_hit=mat,nearest_tested_px=radius))
        for level,p in levels.items():
            for key,uv in p.items():
                if key.endswith('transom') or key=='casement_mid':
                    shot(key,level,uv,[STEEL])
            for a,b in [('outer_left','post'),('post','outer_right')]:
                if a+'_sill' in p and b+'_sill' in p:
                    uv=np.mean([p[a+'_sill'],p[b+'_sill']],axis=0)
                    shot('weathered projected sill',level,(uv+[0,2]).tolist(),[SILL])
    picks={'43052484':[(2,(475,467),[SHADE]),(2,(531,472),[GLASS]),(3,(463,280),[SHADE]),(3,(513,287),[GLASS]),(3,(528,290),[GLASS]),(4,(454,115),[SHADE]),(4,(505,142),[GLASS]),(5,(457,16),[SHADE]),(2,(473,568),[WALL]),(3,(463,360),[WALL])],
           '43052486':[(2,(72,547),[GLASS]),(2,(37,557),[GLASS]),(3,(86,424),[GLASS]),(3,(56,429),[GLASS]),(4,(96,316),[GLASS]),(4,(66,318),[GLASS]),(5,(103,203),[GLASS]),(3,(85,480),[WALL]),(4,(100,361),[WALL])]}
    for code,tests_in_photo in picks.items():
        camera=Camera(code)
        for level,uv,expected in tests_in_photo:shot('clear pane or intervening apron',level,uv,expected)
    return dict(input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),cameras_sha256=hashlib.sha256((HERE/'house-cameras.json').read_bytes()).hexdigest(),
                definition='Original JPEG coordinates. The material of the nearest actual serialized face is retained. A secondary circular search extends to 4 source pixels.',observations=tests,count=len(tests),direct=sum(t['nearest_tested_px']==0 for t in tests),within_four=sum(t['nearest_tested_px'] is not None for t in tests))
if __name__=='__main__':
    args=argparse.ArgumentParser(description=__doc__);args.add_argument('glb',type=Path);args.add_argument('output',type=Path);a=args.parse_args()
    d=verify(a.glb);a.output.write_text(json.dumps(d,indent=2)+'\n');print(d['direct'],d['within_four'],d['count'])
