"""Check the façade optics against independently selected positions in the 2020 exterior photograph."""
from hashlib import sha256
from pathlib import Path
import argparse
import json
import runpy
import numpy as np
from register_court import Camera

HELPER="data/audit/postal-office-v1/independent-glb-review-helpers.py"
PROJECT=next(d for d in Path(__file__).absolute().parents if (d/HELPER).is_file())
M="Shanghai High School hall | "
GLASS="smoked reflecting entrance glass"
WOOD="reddish door timber"
METAL="worn brass pulls"
TRIM="cool grey cast trim"
STONE="dressed stair stone"
YELLOW="ochre render"

def crop_pixel(x,y):
    # Native crop (410,1310)-(980,1565), shown in the working read at 540px width.
    return [round(410+x*570/540),round(1310+y*570/540)]

def face_pixel(x,y):
    return [round(230+x*900/530),round(920+y*900/530)]

MARKS=[]
for i,x in enumerate((49,105,180,231,305,360)):
    MARKS.extend([(f"glazed door {i+1}",crop_pixel(x,134),GLASS),
                  (f"upper transom {i+1}",crop_pixel(x,60),GLASS),
                  (f"bottom timber rail {i+1}",crop_pixel(x,221 if i<3 else 216),WOOD)])
for i,x in enumerate((74,82,204,212,331,339)):
    MARKS.append((f"projected pull {i+1}",crop_pixel(x,160),METAL))
MARKS.extend([("pendant central shaft",face_pixel(248,210),TRIM),
              ("apron left tablet",face_pixel(192,186),TRIM),
              ("apron right tablet",face_pixel(302,181),TRIM),
              ("upper upper triangle",face_pixel(241,91),TRIM),
              ("upper lower triangle",face_pixel(289,138),TRIM),
              ("ochre wall between motifs",face_pixel(254,117),YELLOW)])
for i,y in enumerate([1568,1580,1592,1608,1623,1636,1651]):
    MARKS.append((f"stair surface {i+1}",[640,y],STONE))

def check(path):
    scene=runpy.run_path(str(PROJECT/HELPER))['SerialScene'](path)
    camera=Camera(2020)
    offsets=sorted((round(float(np.hypot(x,y)),3),x,y) for x in range(-4,5)
                   for y in range(-4,5) if x*x+y*y<=16)
    results=[]
    for name,pixel,material in MARKS:
        first=None;best=None
        for dist,x,y in offsets:
            hit=scene.ray(camera.c,camera.ray([pixel[0]+x,pixel[1]+y]),130.)
            if dist==0:first=hit
            if hit and hit['material']==M+material:
                best={'radius':dist,'offset':[x,y]};break
        results.append({'name':name,'pixel':pixel,'expected':M+material,'first':first,'best':best})
    return {'file':path.name,'sha256':sha256(path.read_bytes()).hexdigest(),'source_camera':'2020-10-17',
            'source_pixels':[1500,2000],'count':len(results),'direct':sum(r['best'] and r['best']['radius']==0 or 0 for r in results),
            'within_four':sum(r['best'] is not None for r in results),'results':results}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('glb',type=Path);parser.add_argument('out',type=Path)
    args=parser.parse_args();report=check(args.glb);args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(report['file'],report['direct'],report['within_four'],report['count'])
