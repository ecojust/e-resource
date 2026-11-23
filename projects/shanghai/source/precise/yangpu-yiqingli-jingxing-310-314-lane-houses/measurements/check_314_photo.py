"""Compare independently read facade photograph pixels to unfiltered rays through the finished GLB."""
import argparse
from pathlib import Path
import sys,json
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

def check(path):
    ctl=json.loads((HERE/'314-facade-observations.json').read_bytes())
    reg=json.loads((HERE/'314-open-casement.json').read_bytes())
    mat=np.array(reg['camera_to_rectified']);inverse=np.linalg.inv(mat[:,:3]);eye=-inverse@mat[:,3]
    mesh=SerialScene(path);results=[]
    offsets=[(0,0),(-1,0),(1,0),(0,-1),(0,1),(-2,0),(2,0),(0,-2),(0,2)]
    for name,u,v,feature in ctl['controls']:
        actual=None;match=None
        for dx,dy in offsets:
            direction=inverse@[u+dx,v+dy,1.]
            hit=mesh.ray(eye,direction,65.)
            if dx==dy==0:actual=hit
            if hit and feature in hit['material']:
                match={'offset':[dx,dy],'hit':hit}
                break
        results.append({'name':name,'point':[u,v],'expected':feature,'exact':actual,'match':match})
    return {'mesh':mesh.asset,'exact':sum(bool(v['match'] and v['match']['offset']==[0,0]) for v in results),
            'within_two_pixels':sum(bool(v['match']) for v in results),'count':len(results),'results':results}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();d=check(a.model);a.out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print(d['exact'],d['within_two_pixels'],d['count'],[(r['name'],r['exact']['material'] if r['exact'] else None) for r in d['results'] if not r['match']])
