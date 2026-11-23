"""Check the shared lane, re-entrant corner, outside stairs and garden openings on actual GLBs."""
from pathlib import Path
import numpy as np
import argparse,sys,json,os
HERE=Path(__file__).resolve().parent
PROJECT=next((p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file()),Path(os.environ.get('E_RESOURCE_SHANGHAI','.')))
sys.path[:0]=[str(PROJECT/'source/precise/xuhui-wuyuan-289-garden-houses/source'),str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from glb_triangles import SerialScene
from placement import Facade
from materials import *
def inspect(path):
 scene=SerialScene(path);tests=[]
 def ray(f,tag,origin,destination,expect,travel,tolerance):
    o=np.array(f.point(*origin));dest=np.array(f.point(*destination));hit=scene.ray(o,dest-o,np.linalg.norm(dest-o))
    correct=not hit if expect is None else bool(hit and hit['material'] in expect and abs(hit['distance_m']-travel)<=tolerance)
    tests.append({'house':f.name,'detail':tag,'origin_udz':origin,'end_udz':destination,'materials':expect,'expected_distance_m':travel,'tolerance_m':tolerance,'first_hit':hit,'matched':correct})
 for name in ['1-2','3-4']:
    f=Facade(None,name);north=name=='1-2';height=3.43 if north else 3.65;half=1.26 if north else 1.32
    left,right=(-6.50,-5.08) if north else (-6.09,-4.84)
    for i in [1,4,7]:
        u=(left+right)/2;d=-1.47+(i-.45)*2.01/7;z=i*half/7
        ray(f,'lower flight tread '+str(i),(u,d,z+.17),(u,d,z-.17),(STEP,),.17,.012)
    for i in [1,5,9,13]:
        u=right+(i-.48)*(-1.27-right)/13;z=half+(height-half)*i/13
        ray(f,'upper flight tread '+str(i),(u,.65,z+.17),(u,.65,z-.17),(STEP,),.17,.012)
    # A person can see through the garden porch front under the Tudor arch.
    u=-6.72 if north else -6.55;depth=9.62 if north else 11.20
    ray(f,'garden porch throat',(u-.36,depth-2.20,1.78),(u+.48,depth-2.20,1.78),None,None,0)
    ray(f,'plastered garden pier',(u-.50,depth-4.20,2.82),(u+.38,depth-4.20,2.82),(CREAM,),.50,.025)
    ray(f,'twin chimney outer section',(-2.26 if north else -2.47,1.70,9.45),(-2.26 if north else -2.47,2.55,9.45),(BRICK,),.435,.015)
 f=Facade(None,'1-2')
 for u,d in [(4.5,8.8),(5.7,9.9)]:
    ray(f,'open sky through northern recess',(u,d,13.0),(u,d,.12),None,None,0)
 for z in [3.29,3.37,3.425]:
    ray(f,'recess wall beyond floor edge',(4.4,7.13,z),(4.4,6.23,z),(CREAM,),.63,.015)
    ray(f,'recess lateral wall beyond floor edge',(3.88,9.0,z),(3.02,9.0,z),(CREAM,),.68,.015)
 ray(f,'lane between both houses',(-10,-1.93,3.00),(-10,-1.93,-.11),(PAVE,),3.038,.011)
 return {'mesh':scene.asset,'tested':len(tests),'matched':sum(t['matched'] for t in tests),'rays':tests}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=inspect(a.mesh);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n');print(r['matched'],r['tested'],[(t['detail'],t['first_hit']and t['first_hit']['material'])for t in r['rays']if not t['matched']])
