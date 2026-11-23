"""Read the original balcony rail at eight independent points in the two photos."""
import argparse
import json
from pathlib import Path
from hashlib import sha256
import runpy
import sys
import numpy as np

sys.path.insert(0,str(Path(__file__).absolute().parent))
from windowed_glb import read_windowed

# Coordinates refer to the original photograph or the 2017 quarter-width reading.
# The last two coordinates on each view are on opposite sides of a baluster.
POINTS = {
    2017: [('upper rail centre',1179,257,True), ('bottom rail under middle',1181,348,True),
           ('curved left baluster',1124,307,True), ('opening behind central balusters',1175,305,False)],
    2026: [('upper rail at centre',1419,580,True), ('bottom rail under middle',1413,670,True),
           ('outermost left bend',1364,649,True), ('opening behind central balusters',1425,636,False)]}

def inspect(mesh,cameras,ray_helper):
    camera_class=runpy.run_path(str(cameras/'register_openings.py'))['Camera']
    views={year:camera_class(year,cameras/'two-photo-cameras.json') for year in POINTS}
    marks={}
    bounds={}
    for year,points in POINTS.items():
        scale,shift=(4,1.5) if year==2017 else (1,0)
        native=[(name,np.array([x*scale+shift,y*scale+shift]),iron) for name,x,y,iron in points]
        marks[year]=native
        uv=np.stack([uv for _,uv,_ in native])
        bounds[year]=(uv.min(0),uv.max(0))
    scene,indices,count=read_windowed(mesh,views,bounds,runpy.run_path(str(ray_helper))['SerialScene'])
    result=[]
    for year,rows in marks.items():
        for name,uv,iron in rows:
            hit=scene.ray(*views[year].ray(uv),40)
            if hit:
                hit['triangle_index']=int(indices[hit['triangle_index']])
            seen=bool(hit and hit['material']=='wrought iron')
            result.append({'year':year,'name':name,'native_pixel':uv.tolist(),'photographed_iron':iron,
                           'first_intersection':hit,'model_iron':seen,'matches':iron==seen})
    return {'mesh':mesh.name,'mesh_sha256':sha256(mesh.read_bytes()).hexdigest(),
        'camera_sha256':sha256((cameras/'two-photo-cameras.json').read_bytes()).hexdigest(),
        'triangles':count,'candidate_triangles':len(indices),'points':result,
        'exact_iron_or_gap':sum(p['matches'] for p in result),'tests':len(result)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('report',type=Path)
    p.add_argument('--cameras',type=Path,required=True);p.add_argument('--ray-helper',type=Path,required=True)
    a=p.parse_args();r=inspect(a.mesh,a.cameras,a.ray_helper)
    a.report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['exact_iron_or_gap'],r['tests'])
