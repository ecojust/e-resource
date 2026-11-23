"""First-intersection checks against fixed photo pixels on both balcony leaves and fanlight."""
import argparse
import math
import hashlib
import json
from pathlib import Path
import runpy
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).absolute().parent))
from windowed_glb import read_windowed

# 2017 values were read at quarter scale. Convert the pixel centres once.
READINGS = {
    2017: [
        ('upper fan left pane',1160,115,'glass'),('upper fan right pane',1186,117,'glass'),
        ('inner fan left pane',1164,145,'glass'),('inner fan right pane',1184,145,'glass'),
        ('fan centre bar',1173,140,'wood'),
        ('right open leaf top pane',1218,169,'glass'),('right open leaf middle pane',1220,203,'glass'),
        ('right open leaf lower pane',1221,238,'glass'),('right third crossbar',1216,253,'wood'),
        ('left open leaf upper pane',1128,182,'glass'),('central dark opening',1168,209,'dark')],
    2026: [
        ('upper fan left pane',1414,441,'glass'),('upper fan right pane',1443,440,'glass'),
        ('inner fan left pane',1417,464,'glass'),('inner fan right pane',1438,464,'glass'),
        ('fan centre bar',1428,457,'wood'),
        ('right open leaf top pane',1471,496,'glass'),('right open leaf middle pane',1474,523,'glass'),
        ('right open leaf lower pane',1476,556,'glass'),('right first crossbar',1468,509,'wood'),
        ('left open leaf upper pane',1387,505,'glass'),('central dark opening',1428,528,'dark')],
}
MATERIALS={'glass':'Wukang balcony | cool reflecting glass','wood':'Wukang balcony | dark red painted joinery','dark':'Wukang balcony | shaded recess'}


def inspect(mesh, cameras, ray_helper):
    camera_class=runpy.run_path(str(cameras/'register_openings.py'))['Camera']
    both={y:camera_class(y,cameras/'two-photo-cameras.json') for y in READINGS}
    bounds={}
    for yr,rows in READINGS.items():
        scale,shift,margin=(4,1.5,13) if yr==2017 else (1,0,4)
        marks=np.asarray([[x*scale+shift,y*scale+shift] for _,x,y,_ in rows])
        bounds[yr]=(marks.min(axis=0)-margin,marks.max(axis=0)+margin)
    scene,indices,total=read_windowed(mesh,both,bounds,runpy.run_path(str(ray_helper))['SerialScene'])
    checks=[]
    for year,points in READINGS.items():
        cam=both[year]
        for name,x,y,role in points:
            uv=[4*x+1.5,4*y+1.5] if year==2017 else [x,y]
            eye,direction=cam.ray(uv)
            hit=scene.ray(eye,direction,40)
            if hit:hit['triangle_index']=int(indices[hit['triangle_index']])
            matched=bool(hit and hit['material']==MATERIALS[role])
            nearest=0.0 if matched else None
            tolerance=12 if year==2017 else 3
            if not matched:
                offsets=sorted((dx*dx+dy*dy,dx,dy)
                               for dx in range(-tolerance,tolerance+1)
                               for dy in range(-tolerance,tolerance+1)
                               if 0<dx*dx+dy*dy<=tolerance*tolerance)
                for distance,dx,dy in offsets:
                    eye,direction=cam.ray([uv[0]+dx,uv[1]+dy])
                    neighbor=scene.ray(eye,direction,40)
                    if neighbor and neighbor['material']==MATERIALS[role]:
                        nearest=round(math.sqrt(distance),3)
                        break
            checks.append({'year':year,'feature':name,'native_pixel':uv,'expected':MATERIALS[role],
                           'actual':hit,'matched':matched,'search_radius_native_px':tolerance,
                           'nearest_matching_offset_native_px':nearest})
    return {'mesh':mesh.name,'sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),
            'camera_sha256':hashlib.sha256((cameras/'two-photo-cameras.json').read_bytes()).hexdigest(),
            'triangles_in_input':total,'triangles_in_either_registered_photo_window':len(indices),
            'readings':checks,'tested':len(checks),'matched':sum(row['matched']for row in checks)}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mesh',type=Path)
    parser.add_argument('report',type=Path)
    parser.add_argument('--cameras',type=Path,required=True)
    parser.add_argument('--ray-helper',type=Path,required=True)
    args=parser.parse_args()
    result=inspect(args.mesh,args.cameras,args.ray_helper)
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['matched'],result['tested'])
    for row in result['readings']:
        if not row['matched']:
            print(row['year'],row['feature'],row['actual']['material'] if row['actual'] else None)
