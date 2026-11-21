"""Trace the lane, glazing, tile joints, sill, and rounded bay on each actual export."""
import argparse
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
inspect = runpy.run_path(HERE.parent / 'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']


def probes():
    result = []
    def ray(name, origin, direction, length, materials=None, distances=None):
        result.append(dict(name=name, origin=origin, direction=direction, length=length, allowed=materials, range_m=distances))
    def front(name, x, z, materials, lo, hi):
        ray(name, [x,-2,z], [0,1,0], 5.2, materials, [lo,hi])
    for x in [-1.65,-.75,0,.69,1.11]:
        for z in [.49,1.57,2.85]:
            ray(f'open through lane {x} {z}',[x,-1.1,z],[0,1,0],4.2)
    for x in [-2.38,2.38]:
        for z in [.88,2.01,3.85,6.62,10.73]:
            front(f'grey roadside jamb {x} {z}',x,z,['Speckled grey facade finish'],1.99,2.01)
    for x in [-1.42,0,1.05]:
        ray(f'overhead passage lining {x}',[x,1.33,1.],[0,0,1],3.,['Light grey passage lining'],[2.295,2.305])
        ray(f'passage paving {x}',[x,1.33,1.],[0,0,-1],1.4,['Stone passage paving'],[.995,1.005])
    for x in [-.67,0,.67]:
        for z in [5.31,5.62,6.29]:
            front(f'recessed middle glazing {x} {z}',x,z,['Grey blue window glass'],2.105,2.124)
    for x in [-.3298,.3298]:
        for z in [5.39,5.77,6.56]:
            front(f'steel window vertical {x} {z}',x,z,['Dark steel window framing'],2.06,2.10)
    for x in [-.40,.047,.235]:
        front(f'ochre panel between strips {x}',x,7.04,['Ochre vertical infill strips'],2.058,2.071)
    for x in [-.465,0,.465]:
        front(f'groove in ochre board {x}',x,7.07,['Recessed horizontal joints'],2.048,2.060)
    for course in [0,3,6,9]:
        z=7.42+.082+course*.107
        for x in [-.92,0,.92]:
            front(f'rounded bay band {course} {x}',x,z+.012,['Fine warm grey bay bands'],1.09,1.103)
            front(f'bay surface between bands {course} {x}',x,z+.04,['Speckled grey facade finish'],1.105,1.115)
    for x,mat in [(-.91,'Pale grey blue upper glass'),(-.29,'Cool grey casement glass'),(.29,'Grey blue window glass'),(.91,'Pale grey blue upper glass')]:
        front(f'street bay glazing {x}',x,9.47,[mat],1.15,1.20)
    for x in [-.58,0,.58]:
        front(f'projecting sill underside drip {x}',x,7.405,['Dark sill flashings'],1.08,1.097)
    front('green address background',1.934,2.69,['Dark green lane plate'],2.305,2.326)
    for x in [1.473,1.571,1.856]:
        front(f'guard tiles at pier {x}',x,2.015,['Dark red glazed tile','Alternate red glazed tile','Glazed tile mortar'],2.341,2.365)
    for side in [-1,1]:
        ray(f'beyond cropped frontage {side}',[side*2.72,-1.4,5.44],[0,1,0],5.)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('raw','full','lod','output'):
        parser.add_argument(key,type=Path)
    args=parser.parse_args()
    report={role:inspect(getattr(args,role),probes())for role in ('raw','full','lod')}
    args.output.write_text(json.dumps(report,indent=1,ensure_ascii=False)+'\n')
    for role,s in report.items():print(role,len(s['cases']),[(c['name'],c['first_hit'])for c in s['cases']if not c['passed']],flush=True)
    raise SystemExit(not all(v['passed']for v in report.values()))
