"""Verify clear pedestrian routes and independent sampled section heights inside the actual GLB."""
from pathlib import Path
import argparse,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
sys.path.insert(0,str(HERE.parent/'source'))
from plan import LEVELS,xy

def measure(path):
    mesh=SerialScene(path);records=[]
    y0,y1=xy(551,304)[1],xy(551,195)[1]
    xl=xy(521,245)[0];xr=xy(578,245)[0]
    def record(name,x,y,height,material,above=.45,tol=.025):
        hit=mesh.ray([x,y,height+above],[0,0,-1],above+1.)
        match=bool(hit and abs(hit['point_enu_m'][2]-height)<=tol and material in hit['material'])
        records.append({'name':name,'xy':[float(x),float(y)],'expected_z':height,'material':material,'hit':hit,'pass':match})
    for f,(lo,hi) in enumerate(zip(LEVELS,LEVELS[1:])):
        n=8 if f==0 else 10
        mid=(lo+hi)/2
        for j in [0,n//2,n-1]:
            t=(j+.5)/n
            record(f'level {f+1} outbound tread {j+1}',xl,y0+(y1-y0)*t,lo+(j+1)*(mid-lo)/n,'terrazzo')
            record(f'level {f+1} return tread {j+1}',xr,y1+(y0-y1)*t,mid+(j+1)*(hi-mid)/n,'terrazzo')
        record(f'level {f+1} half landing',0,xy(552,177)[1],mid,'terrazzo')
    for x,y,h,mat in [(0,0,16.55,'limestone'),(-5.16,2.1,16.55,'limestone'),(5.18,2.2,16.55,'limestone'),
                       (0,1.5,20.39,'clay tile'),(.36,5.75,21.04,'ridge')]:
        record('roof independent section',x,y,h,mat,above=2.,tol=.19)
    return {'mesh':mesh.asset,'measured':len(records),'matched':sum(t['pass']for t in records),'rows':records}

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('model',type=Path);cli.add_argument('out',type=Path);a=cli.parse_args()
    q=measure(a.model);a.out.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');print(q['matched'],q['measured'],[(t['name'],t['xy'],t['hit'])for t in q['rows']if not t['pass']])
