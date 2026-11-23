"""Check read-back geometry at unrectified pixels of the two published photographs."""
from pathlib import Path
import argparse,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from glb_triangles import SerialScene
from garden_plane import projection
from arch_brick_and_glass import RIM
from materials import BLOCK,BRICK,DARK,FRAME,GLASS,MID_GLASS,MORTAR,RENDER,SILL,TRIM
RED=(BRICK,);PANE=(GLASS,MID_GLASS,FRAME);WALL=(RENDER,);BLOCK_FACE=(BLOCK,RIM,MORTAR)
POINTS={'camera_2019_publication':[
 ('middle central brick',353,218,RED),('middle brick shoulder',343,193,RED),('middle brick foot',370,254,RED),
 ('upper central brick',345,122,RED),('upper brick lower right',369,137,RED),('ground brick head',361,317,RED),
 ('middle west steel window',316,217,PANE),('middle east steel window',397,235,PANE),
 ('upper west steel window',318,127,PANE),('upper east steel window',391,123,PANE),
 ('ground east window',403,337,PANE),('large left lower steel window',152,342,PANE),
 ('large left middle steel window',155,223,PANE),('left middle inner glazing',175,245,PANE),
 ('render below paired third-storey window',352,155,WALL),('render above left middle window',154,179,WALL),
 ('render between left window and hopper',198,252,WALL),('plaster at central pier left',290,221,WALL),
 ('plaster above lower central arch',355,299,WALL),('render between upper window and strip',417,122,WALL),
 ('right face of rounded wall',477,221,WALL),('right curve below middle window',483,269,WALL),
 ('upper narrow glass register',439,110,BLOCK_FACE),('upper narrow brick interval',443,135,RED),
 ('middle narrow glass register',446,201,BLOCK_FACE),('middle narrow brick interval',450,239,RED),
 ('lower strip upper register',455,325,BLOCK_FACE),('lower strip brick interval',459,361,RED)],
 'camera_2017':[
 ('upper brick left',426,2588,RED),('upper brick right',568,2667,RED),
 ('upper brick foot',526,2713,RED),('middle central brick left',412,3015,RED),
 ('middle central brick right',565,3157,RED),('middle red brick lower edge',423,3250,RED),
 ('lower central brick upper area',443,3541,RED),('wide window left of brick',322,3084,PANE),
 ('wide window right of brick',651,3165,PANE),('render between the two upper windows',506,2833,WALL),
 ('render left of middle window',198,3121,WALL),('left plaster below the inscription',145,3385,WALL),
 ('render above shallow middle arch',495,2902,WALL),('field right of the middle window',780,3120,WALL)]}
def inspect(mesh):
    model=SerialScene(mesh);output={}
    for key,points in POINTS.items():
        p=projection(key);inv=np.linalg.inv(p[:,:3]);eye=-inv@p[:,3];rows=[]
        for name,x,y,accepted in points:
            h=model.ray(eye,inv@[x,y,1],150)
            rows.append(dict(feature=name,upright_pixel=[x,y],accepted=accepted,first_hit=h,matched=bool(h and h['material'] in accepted)))
        output[key]={'tested':len(rows),'matched':sum(r['matched']for r in rows),'points':rows}
    return {'mesh':model.asset,'photographs':output}
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('model',type=Path);cli.add_argument('result',type=Path);a=cli.parse_args()
    out=inspect(a.model);a.result.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    for key,r in out['photographs'].items():print(key,r['matched'],r['tested'],[x['feature'] for x in r['points'] if not x['matched']])
