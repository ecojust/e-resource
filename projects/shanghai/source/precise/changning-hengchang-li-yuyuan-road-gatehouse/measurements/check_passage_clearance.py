"""Measure model-floor and overhead intersections and through sightlines for both editions."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import load_triangles, first_hit

def measure(path):
    triangles,materials,names,asset=load_triangles(path)
    lo=triangles.min(axis=1)
    hi=triangles.max(axis=1)

    def cast(origin,direction,limit):
        end=origin+direction*limit
        subset=np.flatnonzero(np.all(hi>=np.minimum(origin,end)-1e-7,axis=1)&
                              np.all(lo<=np.maximum(origin,end)+1e-7,axis=1))
        if not len(subset):
            return None
        which,distance,hit=first_hit(triangles[subset],origin,direction)
        if not np.isfinite(distance) or distance>limit:
            return None
        return dict(distance_m=round(distance,5),xyz_m=np.round(hit,5).tolist(),
                    first_material=names[materials[subset[which]]])

    through=[]
    for x in (2.25,3.05,3.85):
        for z in (.60,1.60,2.20):
            for y,dy in ((-.30,1),(16.42,-1)):
                origin=np.array([x,y,z])
                stop=cast(origin,np.array([0.,dy,0.]),16.70)
                through.append(dict(origin_m=origin.tolist(),direction_y=dy,
                                    inspected_length_m=16.70,first_obstruction=stop))
    body=[]
    for y in (1.25,4.15,7.25,10.35,13.45):
        origin=np.array([3.05,y,1.6])
        down=cast(origin,np.array([0.,0.,-1.]),2.)
        up=cast(origin,np.array([0.,0.,1.]),5.)
        body.append(dict(y_m=y,first_floor=down,first_overhead=up,
                         clear_height_m=None if not down or not up else round(up['distance_m']+down['distance_m'],5)))
    return dict(asset=asset,through=through,vertical_sections=body,
                unobstructed=sum(row['first_obstruction'] is None for row in through))

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mesh',nargs='+',type=Path)
    ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args()
    results={p.name:measure(p) for p in args.mesh}
    args.output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
