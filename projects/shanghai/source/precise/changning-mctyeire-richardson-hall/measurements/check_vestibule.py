"""Check original-photo material samples through the emitted GLB of the entrance and gallery."""
import argparse
import json
from pathlib import Path
import runpy
import numpy as np
from check_lawn import RAY,measure
from render_vestibule import render_indoor
HERE=Path(__file__).resolve().parent
CHECKS={
 'warm ivory plaster':[(694,693),(1069,662),(595,599),(657,451),(641,778),(1171,751),(1101,627),(618,169),(780,98),(294,577),(808,496)],
 'dark oak':[(770,836),(751,934),(870,850),(914,949),(1092,847),(1113,942)],
 'honey lantern glass':[(796,348),(870,350),(944,355),(856,457),(877,461),(859,500)],
 'bronze-black joinery':[(822,543),(1083,540),(376,469)],
 'polished mottled floor':[(814,1042),(1010,1041)],
}
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('out',type=Path);ap.add_argument('--render',action='store_true');a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    station=json.loads((HERE/'vestibule-station.json').read_text());m=np.array(station['projection'])
    rays=measure(runpy.run_path(str(RAY))['SerialScene'](a.mesh),m,CHECKS)
    rays['camera_source']=station['photo'];rays['frame_px']=station['frame']
    if a.render:rays['render']=render_indoor(a.mesh,a.out/'vestibule-model.jpg',station)
    (a.out/(a.mesh.stem+'-vestibule-rays.json')).write_text(json.dumps(rays,indent=2)+'\n');print(rays['direct'],rays['count'],[(v['pixel'],v['first_hit'],v['nearest_px']) for v in rays['points'] if not v['direct']])
