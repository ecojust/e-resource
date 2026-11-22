"""Check the photographed gable face, plinth, verge slips and roof tile shells."""
from pathlib import Path
import numpy as np
import json,runpy,sys
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parents[2]/'source/precise/huangpu-hefei-592-east-lane-house/source'))
from west_gable_fabric import MATERIAL,SURVEY,BASE,DRAIN,TILES,RIDGE,slope
from hefei_photo_plane import on_side
inspect=runpy.run_path(here.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
def probes():
    cases=[]
    def sample(name,origin,direction,distance,targets,tolerance):
        cases.append(dict(name=name,origin=origin,direction=direction,length=distance+tolerance+.02,
                          range_m=[distance-tolerance,distance+tolerance],allowed=list(targets)))
    for y in [.30,1.90,2.65,3.45,5.69,6.45,7.17,8.25]:
        for z in [1.59,4.45,7.15]:
            sample(f'West limewash Y{y} Z{z}',[-.8,y,z],[1,0,0],.8,[MATERIAL],.013)
        sample(f'Grey plinth Y{y}',[-.7,y,.94],[1,0,0],.686,[BASE],.012)
    for y in (1.34,1.41,1.48,1.55,1.59):
        sample(f'2015 drain opening Y{y}',[-.48,y,.719],[1,0,0],.571,[DRAIN],.011)
    left,right=SURVEY['roof_strip_x_m']
    ridge=SURVEY['inferred_ridge_yz_m'][0]
    for title,end in [('Street',-.32),('Lane',SURVEY['wall_end_y_m'])]:
        count=round(abs(end-ridge)/.265)
        for j in range(1,count,3):
            y=end+(ridge-end)*(j+.50)/count
            sample(f'{title} red verge course {j+1}',[-.62,y,slope(y)+.12],[1,0,0],.62+left-.040,TILES,.009)
            for i in (1,4,7):
                x=left+(right-left)*(i+.50)/8
                sample(f'{title} course {j+1}, curved tile {i+1}',[x,y,slope(y)+.41],[0,0,-1],.193,TILES,.012)
    for f in [.12,.33,.58,.87]:
        x=left+(right-left)*f
        sample(f'Ridge cap {f}',[x,ridge,slope(ridge)+.61],[0,0,-1],.344,[RIDGE],.008)
    return cases
if __name__=='__main__':
    cases=probes()
    out={k:inspect(Path(path),cases) for k,path in zip(('raw','full','lod'),sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    for k,r in out.items():print(k,r['passed'],[(s['name'],s.get('material')) for s in r['cases'] if not s['passed']][:8])
    sys.exit(int(not all(r['passed'] for r in out.values())))
