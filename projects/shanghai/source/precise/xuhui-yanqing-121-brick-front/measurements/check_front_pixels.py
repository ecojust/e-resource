"""Trace the independently marked 2018 street-face pixels through the delivered GLB."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from render_front import HERE,PRECISE,projection
sys.path.insert(0,str(PRECISE/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from brick_finishes import GREY_BRICK,RED_BAND,HERRINGBONE
from materials import GLASS,GREEN,CREAM,PALE,DARK
POINTS={GREY_BRICK:[(892,240),(748,233),(526,246),(558,265),(363,273),(244,280),(164,280),(463,488),(528,550),(882,567)],GLASS:[(812,231),(831,248),(602,239),(633,264),(451,242),(477,263),(309,261),(325,270),(109,279),(857,511)],HERRINGBONE:[(815,345),(834,363),(304,355),(315,378),(116,378)],RED_BAND:[(784,257),(854,255),(651,257),(340,294),(903,301),(906,550)],GREEN:[(643,491),(669,540)],CREAM:[(909,139),(700,155)],PALE:[(905,61),(610,107)]}
def check(mesh):
    s=SerialScene(mesh);p=projection();inv=np.linalg.inv(p[:,:3]);eye=-inv@p[:,3];rows=[]
    for material,pixels in POINTS.items():
        for x,y in pixels:
            hit=s.ray(eye,inv@[x,y,1],120);actual=hit['material'] if hit else None
            rows.append(dict(pixel=[x,y],expected=material,observed=actual,matched=material==actual))
    return {'source':'Antigng, 2018-02-07 (1300-pixel working copy)','sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),'matched':sum(v['matched'] for v in rows),'count':len(rows),'measurements':rows}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mesh',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args();r=check(args.mesh);args.output.write_text(json.dumps(r,indent=2)+'\n');print(r['matched'],r['count'])
