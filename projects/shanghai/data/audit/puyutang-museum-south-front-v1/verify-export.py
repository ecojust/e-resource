"""Intersect the actual courtyard windows, masonry, door panels and sign on three exported meshes."""
import json,runpy,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

AUDIT=Path(__file__).absolute().parent
PROJECT=AUDIT.parents[2]
SRC=PROJECT/'source/precise/huangpu-puyutang-museum-south-front'
sys.path.insert(0,str(SRC/'source'));sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from south_front import opening_rect,WOOD,GLASS,EDGE,PAR,TILE,TILE2
from material_names import MATERIAL
from photo_plane import position
from museum_sign import METAL
inspect=runpy.run_path(PROJECT/'data/audit/central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def cases():
    dest=[]
    def ray(label,x,z,y,mat):
        dest.append(dict(name=label,origin=[float(x),-2.,float(z)],direction=[0,1,0],length=4.,range_m=[2+y-.004,2+y+.004],allowed=[mat]))
    data=json.loads((SRC/'measurements/observed-frontage.json').read_bytes())
    for row in data['openings']:
        x,z,r,t=opening_rect(row['outline_px'],0.,'wide').bounds
        name=row['level']+' '+str(row['bay']);w=r-x;h=t-z
        ray(name+' glass',x+.159*w,z+.674*h,.139,GLASS)
        ray(name+' centre stile',x+.50*w,z+.677*h,.073,WOOD)
        if row['level']!='lower-door':
            ray(name+' visible sill',x+.45*w,z-.025,-.093,EDGE)
        ray(name+' brick header',x+.33*w,t+.058,-.047,MATERIAL)
    window=opening_rect([(345,393),(439,405),(444,572),(352,565)],-.12)
    x,z,r,t=window.bounds
    for i in range(4):ray('portal upper light '+str(i),x+(i+.5)*(r-x)/4,z+.683*(t-z),-.065,GLASS)
    door=opening_rect([(267,780),(510,779),(522,1062),(272,1083)],-.09)
    x,z,r,t=door.bounds
    for i in range(4):
        ray('entry glass '+str(i),x+(i+.5)*(r-x)/4,z+.53*(t-z),-.016,GLASS)
        ray('entry lower inset '+str(i),x+(i+.5)*(r-x)/4,z+.13*(t-z),-.100,PAR)
    layout=json.loads((SRC/'measurements/museum-sign-layout.json').read_bytes())
    glyphs=json.loads((SRC/'measurements/museum-sign-lettering.json').read_bytes())['glyphs']
    board=np.array(layout['board_corners_px'])
    for letter,entry in zip(glyphs,layout['characters']):
        corners=np.array(entry['source_quad_px'])
        shapes=unary_union([Polygon(r[0],r[1:]) for r in letter['shapes']])
        witness=shapes.buffer(-.009).representative_point()
        u,v=witness.x,witness.y
        uv=(1-u)*(1-v)*corners[0]+u*(1-v)*corners[1]+u*v*corners[2]+(1-u)*v*corners[3]
        x,_,z=position(*uv,-.251);ray('inscription '+letter['char'],x,z,-.251,METAL)
    for x in [-18.,-9.,8.,17.]:
        for y in [.36,1.42,2.31]:
            dest.append(dict(name=f'roof slope {x} {y}',origin=[x,y,13.],direction=[0,0,-1],length=7.,range_m=None,allowed=[TILE,TILE2]))
    return dest

if __name__=='__main__':
    paths=list(map(Path,sys.argv[1:]));samples=cases();names=['raw','full','lod'] if len(paths)==4 else ['model']
    out={n:inspect(f,samples)for n,f in zip(names,paths[:-1])}
    paths[-1].write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n')
    failed={n:[(q['name'],q['first_hit'])for q in v['cases']if not q['passed']]for n,v in out.items()}
    print(len(samples),failed);sys.exit(int(any(failed.values())))
