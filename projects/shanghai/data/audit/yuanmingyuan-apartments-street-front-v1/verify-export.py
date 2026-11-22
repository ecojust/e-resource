"""First-surface checks on the entrance, cast lettering and the two brick corner loggias."""
import json
from pathlib import Path
import runpy
import sys

import numpy as np
from shapely.geometry import Polygon

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
SRC=PROJECT/'source/precise/huangpu-yuanmingyuan-apartments-street-front/source'
sys.path.insert(0,str(SRC))
from east_photo_plane import on_wall
from east_facade import BED,CORNICE,OAK,PLASTER,TERRA,curve_point
from material_names import MATERIAL
from street_entrance import AWNING,DAMP,FANGLASS,GLASS,GRANITE,INNER,METAL,STONE,WOOD
from wing_casements import GLASS as SASH_GLASS
from english_name import STROKES
inspect=runpy.run_path(PROJECT/'data/audit/central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
MEASURES=SRC.parent/'measurements'


def cases():
    probes=[]
    def ray(name,start,direction,mat,dmin,dmax):
        probes.append(dict(name=name,origin=np.asarray(start).tolist(),direction=np.asarray(direction).tolist(),
             length=dmax+.075,allowed=[mat] if isinstance(mat,str) else mat,range_m=[dmin,dmax]))
    def front(name,x,z,y0,y1,mat):
        ray(name,[x,-2,z],[0,1,0],mat,y0+2,y1+2)
    def front_photo(name,u,v,y0,y1,mat):
        p=on_wall(u,v,(y0+y1)/2,'2016_front');front(name,p[0],p[2],y0,y1,mat)
    for u in [499.6,528.4,673.9,704.3]:
        for v in [479.,508.,538.]:
            p=on_wall(u,v,1.025,'2016_front')
            front(f'Four columns at {u:g}, sample {v:g}',p[0],p[2],.755,.89,STONE)
    for k,u in enumerate([233.,384.,822.,968.],1):
        for v in [476.,500.,532.]:
            front_photo(f'Shop {k} visible glass at {v:g}',u,v,.225,.234,GLASS)
    for u,v in [(519,593),(682,585),(519,615),(682,613)]:
        front_photo(f'Shared column brick pedestal at {u}:{v}',u,v,.813,.829,MATERIAL)
    for x in [-10.9,-7.33,-3.62,3.38,7.02,10.95]:
        for z in [8.53,13.73,17.74]:
            front(f'Rendered wing at {x:g} / {z:g}',x,z,-.012,.012,PLASTER)
    for u,v,mat,y0,y1 in [(586,483,FANGLASS,2.83,2.92),(610,482,FANGLASS,2.83,2.92),
                            (597,560,INNER,4.09,4.14),(598,575,INNER,4.09,4.14)]:
        front_photo(f'Shaded doorway at {u}:{v}',u,v,y0,y1,mat)
    for x in [-.6,0,.61]:
        ray('Stone inner landing '+str(x),[x,3.02,1.2],[0,0,-1],GRANITE,.86,.89)
    # A point from every connected cast character and its neighbouring stone
    # verifies both the lettering and the true plane determined by stereo.
    lettering=json.loads((MEASURES/'five-entrance-characters.json').read_bytes())
    for letter in lettering['letters']:
        shapes=[Polygon(s['shell'],s['holes']) for s in letter['strokes']]
        outline=max(shapes,key=lambda p:p.area)
        from shapely.ops import polylabel
        point=polylabel(outline,tolerance=.12)
        p=on_wall(point.x,point.y,.737)
        front('Cast metal glyph '+letter['character'],p[0],p[2],.719,.737,METAL)
    for x in [-2.09,-.95,.02,1.,2.04]:front(f'Inscription backing {x:g}',x,5.33,.732,.759,STONE)
    letters=json.loads((MEASURES/'english-entrance-layout.json').read_bytes())
    for j,(c,m,width) in enumerate(letters['letters'],1):
        line=STROKES[c][0];a=np.array(line[0]);b=np.array(line[1]);x,z=(a+b)*.5
        u=m+(x-.5)*width;v=np.interp(u,[495,707],[383.4,382])-z*letters['height_px']
        p=on_wall(u,v,letters['front_depth_m'],'2016_front')
        front(f'English cast capital {j} {c}',p[0],p[2],.808,.832,METAL)
    for side,tag in [(-1,'south'),(1,'north')]:
        base=np.array([side*11.729,0.]);tv=np.array([side*5.24,5.0]);tv/=np.linalg.norm(tv);inn=np.array([-side*tv[1],abs(tv[0])]);rot=np.column_stack((tv,inn))
        for j,t in enumerate([-.76,-.40,0.,.40,.76],1):
            a=t*1.35
            outer=np.array([np.sin(a),-np.cos(a)])
            for z,proj,material,name in [(5.16,0.,STONE,'architrave'),(5.55,.035,BED,'terracotta bed'),(6.05,.151,CORNICE,'upper stone drip'),(6.73,.026,MATERIAL,'curved brick parapet')]:
                p=base+rot@curve_point(t,proj);n=rot@outer
                ray(f'{tag} loggia {name} {j}',[*p+n,z],[*-n,0],material,.986,1.012)
        for j,(s,z) in enumerate([(1.56,8.45),(1.52,13.02),(1.47,17.53)],1):
            p=base+rot@np.array([s,-1.5]);ray(f'{tag} chamfer sash {j}',[*p,z],[*inn,0],SASH_GLASS,1.68,1.97)
    return probes


if __name__=='__main__':
    probes=cases()
    results={n:inspect(Path(f),probes) for n,f in zip(('raw','full','lod'),sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    failures={k:[(x['name'],x['first_hit'])for x in row['cases'] if not x['passed']]for k,row in results.items()}
    print(len(probes),failures)
    sys.exit(int(any(failures.values())))
