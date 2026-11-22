"""Test the street-facing plaster, projecting details, joints, rack and passage in the actual exported mesh."""
from pathlib import Path
import json
import runpy
import sys

HERE=Path(__file__).resolve().parent
SRC=HERE.parents[2]/'source/precise/huangpu-xiai-hengai-common-lane-gate/source'
sys.path.insert(0,str(SRC))
from gatehouse_fabric import STONE,EDGE,IRON,FLOOR,SEAM,survey
from material_names import MATERIAL
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def probes():
    lines=survey()
    tests=[]
    def sample(label,x,z,y,material,origin=-.9,tol=.009):
        distance=y-origin
        tests.append(dict(name=label,origin=[x,origin,z],direction=[0,1,0],length=distance+tol+.018,
                          allowed=[material],range_m=[distance-tol,distance+tol]))
    for column,x in enumerate([-2.89,-2.53,2.12,2.59]):
        for z in [3.96,4.90,5.51,6.18,6.73,7.53]:
            sample(f'Side plaster {column+1}, Z{z}',x,z,0,MATERIAL)
        for z in [4.33,5.02,5.76,6.48]:
            sample(f'Inset rendering joint {column+1}, Z{z}',x,z,.016,SEAM)
    for x in [-2.88,-1.99,-.86,.14,1.14,2.32,2.81]:
        sample(f'Upper cornice bed X{x}',x,lines['cornice_lower']+.021,-.062,EDGE)
        sample(f'Upper cornice rounded nose X{x}',x,lines['cornice_lower']+.071,-.119,STONE)
        sample(f'Upper cornice drip X{x}',x,lines['cornice_upper']-.015,-.154,STONE)
    for x in [-1.48,-.93,-.42,.50,1.25]:
        sample(f'Panel sill lip X{x}',x,lines['sill_course_top']-.021,-.149,STONE)
        sample(f'Apron course X{x}',x,lines['panel_band_top']-.020,-.095,STONE)
    for z in [4.976,5.112,5.251,5.395]:
        for x in [-.56,-.25,-.023,.15]:
            sample(f'Folded front rail X{x} Z{z}',x,z,-.501,IRON)
    for x in [-.54,-.32,-.16,.13]:
        sample(f'Projecting tray X{x}',x,4.892,-.516,FLOOR)
    for x in [-.90,-.36,.07,.73,1.10]:
        for z in [1.18,1.54,2.19]:
            tests.append(dict(name=f'Clear public passage X{x} Z{z}',origin=[x,-.72,z],
                              direction=[0,1,0],length=1.18,range_m=None,allowed=None))
    return tests

if __name__=='__main__':
    cases=probes()
    rows={k:inspect(Path(p),cases)for k,p in zip(['raw','full','lod'],sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    for k,r in rows.items():
        print(k,len(r['cases']),[(c['name'],c.get('hit'))for c in r['cases']if not c['passed']][:12])
    sys.exit(int(not all(r['passed']for r in rows.values())))
