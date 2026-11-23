"""Cast photo-space rays through the central wall openings and joining balcony in the delivered mesh."""
from pathlib import Path
import argparse
import hashlib
import json
import runpy
import sys

def inspect(project,mesh):
    src=project/'source/precise/xuhui-yuqing-80-twin-winter-gardens'
    sys.path.insert(0,str(src/'measurements'));sys.path.insert(0,str(src/'source'))
    from register_garden import Camera
    from central_front import COPING,PLASTER,FRAME,GLASS,PANEL,CERAMIC,PIPE,RAILING
    reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    scene=reader['SerialScene'](mesh)
    # These observations are read from the photograph, in three explicitly defined image crops.
    def up(x,y):return [x*3980/680*1080/4912,y*3980/680*1080/4912]
    def ground(x,y):return [(710+x*1400/325)*1080/4912,(1350+y*1400/325)*1080/4912]
    def southwest(x,y):return [x*934/720,y*934/720]
    tests=[
        (4,'upper wide window, left daylight',up(210,152),[GLASS]),
        (4,'upper wide window, right daylight',up(243,145),[GLASS]),
        (4,'upper horizontal window',up(350,111),[GLASS,FRAME]),
        (4,'upper circular fan casing',up(293,119),[COPING,FRAME]),
        (4,'southwest dark drain',up(167,179),[PIPE]),
        (4,'upper bridge front panel',up(343,145),[PLASTER]),
        (4,'middle recessed window',up(347,224),[FRAME,GLASS]),
        (4,'wide lower casement',ground(258,215),[GLASS,FRAME]),
        (4,'lower casement opaque base',ground(260,278),[PANEL]),
        (4,'far lower casement',ground(119,200),[FRAME,GLASS]),
        (4,'middle round support',ground(158,199),[CERAMIC]),
        (4,'long terrace panel above floor',ground(175,55),[PLASTER]),
        (6,'upper white fan unit',southwest(448,143),[COPING,FRAME]),
        (6,'straight balcony between winter gardens',southwest(485,299),[PLASTER]),
        (6,'curved head of middle support',southwest(490,362),[CERAMIC]),
    ]
    result=[]
    for n,desc,uv,materials in tests:
        cam=Camera(n)
        def first(dx,dy):
            return scene.ray(cam.c,cam.ray([uv[0]+dx,uv[1]+dy]),85)
        hit=first(0,0);offset=None
        for _,x,y in sorted((x*x+y*y,x,y)for x in range(-5,6)for y in range(-5,6)if x*x+y*y<=25):
            h=first(x,y)
            if h is not None and h['material'] in materials:offset=[x,y];break
        result.append(dict(view=n,feature=desc,expected=materials,pixel=uv,first_hit=hit,within_five_px_offset=offset))
    return dict(file=mesh.name,sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),results=result,
                exact=sum(bool(r['first_hit'] and r['first_hit']['material'] in r['expected']) for r in result),
                within_five=sum(r['within_five_px_offset'] is not None for r in result),total=len(result))

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('project',type=Path);a.add_argument('mesh',type=Path);a.add_argument('result',type=Path);args=a.parse_args()
    result=inspect(args.project,args.mesh);args.result.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['exact'],result['within_five'],result['total'])
