"""Check the canopy, porch, gate, folded stair lights and individual landing spandrels."""
from pathlib import Path
from math import cos, pi, sin
import argparse
import json
import runpy

HERE=Path(__file__).resolve().parent
trace=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']


def cases():
    tests=[]
    def probe(name, origin, direction, material=None, limits=None):
        tests.append(dict(name=name,origin=list(origin),direction=list(direction),length=3.5,
                          allowed=[material] if isinstance(material,str) else material,range_m=limits))
    def front(name, x, z, material=None, lo=None, hi=None):
        probe(name,(x,-2,z),(0,1,0),material,[lo,hi] if material else None)
    for x in (-1.08,1.08):
        for z in (3.15,4.8,7.9,10.8,14.7,17.68):
            front(f'full-height cement pier {x} {z}',x,z,'Ivory cement render',1.625,1.645)
    for x in (-1.135,1.135):
        for z in (.22,1.36,2.29,2.58):
            front(f'canopy column {x} {z}',x,z,'Warm cement canopy columns',.953,1.005)
    for x in (-1.58,-.65,0,.65,1.58):
        front(f'projecting square canopy {x}',x,2.81,'Ivory cement render',.67,.71)
    for x in (-.51,-.39,.39,.51):
        front(f'gate horizontal louver {x}',x,.92,'Bottle green gate',2.144,2.170)
    # The existing photograph shows the closed top rail from the front. Test the
    # whole lintel separately from the recessed backing beside it.
    for x in (-.60,0,.60):
        front(f'top of the green gate {x}',x,2.21,'Bottle green gate',2.12,2.14)
    for x in (-.713,.713):
        front(f'dark reveal beside leaf {x}',x,1.87,'Shade inside vestibule',2.26,2.29)
    front('enamel door number',-.221,2.39,'Green enamel address plate',1.880,1.905)
    for x in (-.80,.80):
        for z in (.61,1.59,2.02):
            front(f'terracotta door return {x} {z}',x,z,'Dark red entrance render',1.89,1.92)
    # Original drawing bounds on the right are x=587 and x=662. With four lights
    # the central mullion is at 624.5 px; 633.875 px is in the adjacent pane.
    for height in (2.04,5.50,8.76,12.21):
        front(f'right bay central steel mullion {height}',2.68,height,'Oxide red window steel',2.26,2.28)
    for x in (-2.80,(633.875-519)*.02546684210526316):
        for z in (2.04,5.50,8.76,12.21):
            front(f'side bay glass {x} {z}',x,z,['Grey green stair glass','Cloud reflection in glass'],2.30,2.39)
    # On each facet the probes point straight at its own plane. A flat central strip would miss them.
    span=.71307158
    run=(span**2+.66**2)**.5
    def facet(sign,u,height,name,material,limits):
        tangent=(span/run,sign*.66/run)
        normal=(tangent[1],-tangent[0])
        center=(sign*span/2,-.45)
        origin=[center[0]+u*tangent[0]+2*normal[0],center[1]+u*tangent[1]+2*normal[1],height]
        probe(f'{name}, facet {sign}, tangent {u:.2f}, {height:.2f} metres',origin,[-normal[0],-normal[1],0],material,limits)
    for sign in (-1,1):
        for z in (3.91,7.09,10.29,13.54):
            for u in (-.20,.20):
                facet(sign,u,z,'folded stair glazing',['Grey green stair glass','Cloud reflection in glass'],[2.064,2.086])
            facet(sign,0,z,'steel center mullion','Oxide red window steel',[1.996,2.018])
        for z,mat in [(3.124,'Painted lower brick band'),(6.30,'Weathered red facing brick'),
                      (9.68,'Weathered red facing brick'),(12.66,'Weathered red facing brick')]:
            facet(sign,.12,z,'brick-faced landing',mat,[1.902,1.922])
    # On-axis probes detect an open mitre, even if both oblique faces look complete from the side.
    crown_low=(705-118)*.02546684210526316+.020
    tower_top=(705-4)*.02546684210526316
    crown_pitch=(tower_top-crown_low-.10)/8
    for i in range(8):
        for x in (-.08,0,.08):
            front(f'continuous folded crown fin {i} near its apex {x}',x,crown_low+.09+i*crown_pitch,
                  'Pale folded crown bands',.82,.94)
    for x in (-.03,0,.03):
        front(f'lower continuous folded brick return {x}',x,3.124,'Painted lower brick band',1.08,1.16)
    for x in (-4.15,4.15):
        front(f'edge of photograph-limited elevation {x}',x,6.4)
    for x in (-2.28,2.28):
        front(f'open sky beside tower {x}',x,17.2)
    return tests


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('raw','full','lod','output'):
        parser.add_argument(key,type=Path)
    args=parser.parse_args()
    result={role:trace(getattr(args,role),cases())for role in ('raw','full','lod')}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    for role,row in result.items():
        print(role,len(row['cases']),[(v['name'],v['first_hit']) for v in row['cases']if not v['passed']],flush=True)
    raise SystemExit(not all(row['passed']for row in result.values()))
