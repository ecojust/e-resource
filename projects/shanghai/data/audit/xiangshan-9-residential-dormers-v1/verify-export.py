"""Read the finished street-wall surfaces, casement panes, shutters and main tiled eaves."""
from pathlib import Path
import json
import runpy
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/huangpu-xiangshan-9-residential-dormers/source'
sys.path.insert(0,str(SOURCE))
from xiangshan_frontage import WINDOWS,MATERIAL,STONE,SASH,GLASS,SHUTTER,SOFFIT,TILES
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def rays():
    checks=[]
    def probe(name,origin,direction,allowed,distances):
        checks.append(dict(name=name,origin=list(origin),direction=list(direction),length=distances[1]+.02,
                           allowed=allowed,range_m=list(distances)))
    for w in WINDOWS:
        left,right,bottom,top=(w[k] for k in ('left','right','bottom','top'))
        label=w['label']
        probe(label+' lintel',[(left+right)/2,-.5,top+.039],[0,1,0],[STONE],(.38,.42))
        probe(label+' sill',[left+.2,-.5,bottom-.034],[0,1,0],[STONE],(.38,.42))
        for x in (left+.0225,right-.021):
            probe(label+f' casing {x:.2f}',[x,.013,bottom+.24],[0,1,0],[SASH],(.08,.092))
        xs=np.linspace(left+.045,right-.045,w['columns']+1)
        zs=np.linspace(bottom+.05,top-.05,w['rows']+1)
        for i,(a,c) in enumerate(zip(xs,xs[1:])):
            for j,(za,zb) in enumerate(zip(zs,zs[1:])):
                probe(label+f' pane {i+1}.{j+1}',[(a+c)/2,.01,(za+zb)/2],[0,1,0],[GLASS],(.143,.151))
    for x in (-10.33,-7.55,-5.05,-2.60,.09,2.69,3.93):
        for z in (5.35,7.81):
            probe(f'Roughcast {x},{z}',[x,-.5,z],[0,1,0],[MATERIAL],(.495,.505))
    for x in (2.51,2.75,3.20,3.56):
        for z in (1.61,2.27,2.79,3.32):
            probe(f'Timber louvre {x},{z}',[x,-.15,z],[0,1,0],[SHUTTER],(.19,.29))
    for x in (-7.95,-7.28,-6.51,-5.91,-4.88,-3.84):
        for y in (-1.17,-.69,-.21):
            z=4.88+.83*y/1.32
            probe(f'Lower clay canopy {x},{y}',[x,y,z+.32],[0,0,-1],TILES,(.27,.329))
    return checks
if __name__=='__main__':
    results={role:inspect(Path(path),rays()) for role,path in zip(('raw','full','lod'),sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    for role,r in results.items():
        print(role,len(r['cases']),[(c['name'],(c['first_hit'] or {}).get('material')) for c in r['cases'] if not c['passed']])
    sys.exit(int(not all(v['passed'] for v in results.values())))
