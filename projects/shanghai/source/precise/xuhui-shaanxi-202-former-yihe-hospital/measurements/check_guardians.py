"""Compare photographed highlights and supports on both guardian lions with direct triangle intersections."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import numpy as np
from fit_guardians import POINTS, sample_px, wide
from register_court import Camera

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'data/audit/postal-office-v1/independent-glb-review-helpers.py').is_file())
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
GREY=('Yihe guardians | grey granite plinth','Yihe guardians | grey dressed coping')
CARVED=('Yihe guardians | warm pale carved stone','Yihe guardians | sheltered stone recess')

def inspect(path):
    scene=runpy.run_path(str(READER))['SerialScene'](path)
    close=json.loads((HERE/'entrance-cameras.json').read_bytes())['close_view']
    center=np.array(close['C'])
    inverse=np.array(close['R']).T@np.linalg.inv(close['K'])
    reports=[]
    def examine(name,label,uv,c,ray,side,expected):
        def compare(offset):
            direction=ray(uv+offset)
            hit=scene.ray(c,direction,70)
            passed=bool(hit and hit['material'] in expected and abs(hit['point_enu_m'][0]-side)<.44)
            return hit,passed
        first,direct=compare([0,0]);nearest=None
        for r,dx,dy in sorted((np.hypot(x,y),x,y) for x in range(-5,6)for y in range(-5,6)if np.hypot(x,y)<=5):
            hit,passed=compare([dx,dy])
            if passed:
                nearest={'distance_px':float(r),'offset_px':[dx,dy],'hit':hit};break
        reports.append(dict(photo=name,feature=label,source_uv=uv.tolist(),exact=direct,first=first,nearest=nearest))
    for label,(uv,_xyz) in POINTS.items():
        examine('06',label,sample_px(uv),center,lambda p:inverse@np.r_[p,1.],.408,CARVED)
    for label,uv,material in [('inner eye surround',[119,120],CARVED),('outer curled ear',[275,111],CARVED),
                             ('chest and pendant',[193,336],CARVED),('coping below pale stone',[186,717],GREY)]:
        examine('06',label,sample_px(uv),center,lambda p:inverse@np.r_[p,1.],.408,material)
    for side,record in wide().items():
        for photo,xy in zip(['commons','05','10'],record['working_pixels']):
            camera=Camera(photo)
            # In wide frames the independently marked crown lies on the background boundary.
            # Enter the photographed ruff by three pixels to test the material of the visible stone.
            examine(photo,side+' crown interior 3px below upper contour',np.array(xy)+[0,3],camera.c,camera.ray,
                    -2.782 if side=='left' else .408,CARVED)
    return {'mesh_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'observations':reports,
            'exact':sum(r['exact'] for r in reports),'within_five_working_px':sum(r['nearest'] is not None for r in reports),
            'total':len(reports),'limits':'The front paw of the right guardian rests on a carved ball. Plants and vehicles obscure the lower part in independent garden views. The left raised-paw motif is unresolved.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();r=inspect(a.mesh);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['exact'],r['within_five_working_px'],r['total'],r['mesh_sha256'])
