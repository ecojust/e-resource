"""First surfaces on masonry, parapet courses and drainpipes in the street photograph."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from frontage_coordinates import FRONT_CAMERA,facade_point
from glb_triangles import SerialScene
from terrace_wall import PLASTER,RED,BUFF,CREAM,TERRA,IRON,CORNICE

READINGS=[
 ('grey running bond',[PLASTER],[(75,222),(154,224),(248,222),(258,250),(636,216),(717,257),(817,224),(142,339),(238,357),(650,351),(732,354)]),
 ('red brick field',[RED],[(353,220),(434,227),(533,219),(613,218),(349,350),(435,354),(541,352),(614,360)]),
 ('red voussoirs',[*TERRA,RED],[(121,176),(216,177),(317,184),(396,183),(494,184),(575,185),(674,175),(777,175),
                                    (108,294),(206,295),(310,296),(397,296),(492,296),(582,297),(688,295),(785,296)]),
 ('pale spandrel',[CREAM],[(108,249),(209,250),(314,256),(393,255),(492,255),(578,256),(681,250),(797,252),
                           (98,378),(199,384),(304,385),(393,383),(684,384)]),
 ('continuous eave',[CORNICE,RED],[(313,154),(411,154),(478,154),(570,154)]),
 ('left downpipe',[IRON],[(170.97,177),(165.67,217),(157.32,279),(149.33,336),(143.01,381)]),
 ('centre downpipe',[IRON],[(445.49,177),(445.86,217),(445.81,279),(445.57,336),(445.6,381)]),
 ('right downpipe',[IRON],[(725.91,177),(731.05,217),(739.52,279),(748.13,336),(754.72,381)])]

def inspect(asset):
    scene=SerialScene(asset);eye=-np.linalg.solve(FRONT_CAMERA[:,:3],FRONT_CAMERA[:,3]);rows=[]
    for feature,accepted,pixels in READINGS:
        for u,v in pixels:
            point=np.array(facade_point(u,v,0))
            hit=scene.ray(eye,point-eye,np.linalg.norm(point-eye)+.75)
            mat=hit['material']if hit else None
            rows.append(dict(feature=feature,uv=[u,v],accepted=accepted,first_material=mat,passed=mat in accepted))
    return dict(asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),photograph_sha256='7ddbb51fe26c69b638bbaa855692ccd69f2c6820788d7f3917f39085792fad2f',
                total=len(rows),hits=sum(r['passed']for r in rows),passed=all(r['passed']for r in rows),readings=rows)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('asset',type=Path);ap.add_argument('out',type=Path)
    a=ap.parse_args();r=inspect(a.asset);a.out.write_text(json.dumps(r,indent=1)+'\n');print(r['hits'],r['total'])
    for v in r['readings']:
        if not v['passed']:print(v['feature'],v['uv'],v['first_material'])
    raise SystemExit(int(not r['passed']))
