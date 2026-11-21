"""Read entrance openings, timber-and-glass joinery and roof details from all three delivered meshes."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
ID = 'xuhui-dingxiang-garden-main-house'
SerialScene = runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
DECODER = PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'


def probes(path, simplified=False):
    mesh = SerialScene(path)
    checks = []

    def cast(label, origin, direction, expected, length=7, distance=None):
        hit = mesh.ray(origin, direction, length)
        passed = (hit is None if expected is None else
                  hit is not None and hit['material'] == expected
                  and (distance is None or abs(hit['distance_m']-distance) <= .008))
        checks.append(dict(label=label, origin=origin, direction=direction, length=length,
                           first_surface=expected, expected_distance_m=distance, hit=hit, passed=passed))

    def normal(label,x,z,material,depth=None,length=7):
        cast(label,[x,-4,z],[0,1,0],material,length,depth)

    for x in (1.14-.47,1.14,1.14+.47):
        normal('clear through upper arched vent',x,3.60,None,length=2.15)
        normal('head above each arched vent',x,3.88,'warm roughcast',1.57)
    for x in (.27,.72,1.14,1.56,2.01):
        crown=2.40+.9516*(1-((x-1.14)/.9516)**2)**.5
        normal('open below the arch curve',x,crown-.049,None,length=2.2)
        normal('masonry above the arch curve',x,crown+.048,'warm roughcast',1.57)
    for x in (.05,2.23):
        normal('grey projecting spring blocks',x,2.326,'dark corbel stone')
        normal('clear gap between the two spring blocks',1.14,2.326,None,length=3)
    for x in (-.27,2.55):
        normal('front pier below the number',x,1.58,'warm roughcast',1.57)
    normal('enamel number on the right pier',2.38,2.99,'enamel numeral')
    normal('brass plate beside the numeral',2.30,3.01,'brass address plate')
    normal('inner timber door panel at end of porch',1.39,.80,'oxblood timber')
    for x in (.67,1.50):
        normal('glazed door beyond porch',x,1.67,'inner door glazing',4.255)
    for y in (-1.83,-1.21,-.65):
        cast('side arch open through both returns',[-1.2,y,1.50],[1,0,0],None,4.30)
    for i in range(3):
        cast('separate stone tread',[1.14,-2.43-.67+.22*i,1.5],[0,0,-1],'grey stone tread',3,1.5-(i+1)*.104)
    for x in (-2.15,-1.11):
        normal('glass in upper narrow window',x-.16,5.43,'lead grey glass',4.26)
        normal('upper window transom',x,5.58,'oxblood timber')
    for x in (-3.73,-3.04,-.31,.43,1.16,1.94,2.66,3.42):
        normal('timber stud in upper wall',x,7.20,'oxblood timber',3.888)
        normal('render infill beside stud',x+.16,7.20,'warm roughcast',4)
    for x in (-2.45,-2.05,-1.56,-1.00,-.60):
        normal('oriel projecting lower sill',x,7.65,'oxblood timber')
    for i in range(4):
        x=-2.55+(i+.45)*2.03/4
        normal('projecting window glazing',x,8.68,'lead grey glass',3.585)
    normal('upper transom in the projecting oriel',-1.84,7.72+(9.17-7.72)*.736,'oxblood timber')
    for x in (-2.47,-2.06,-1.01,-.60):
        cast('bracket beneath oriel',[x,-.19,7.0],[0,0,1],'weathered bargeboard',2)
    for x in (-3.67,-2.52,1.80,3.53):
        cast('red clay roof surface',[x,1.75,15],[0,0,-1],'earthen roof tiles',8)
    cast('capped roof ridge',[0,.88,15],[0,0,-1],'earthen roof tiles',8)
    for x,y in ((-2.11,2.44),(2.95,3.30)):
        cast('each chimney coping',[x,y,15],[0,0,-1],'grey moulded stone',8)
    for course in (6,7,8):
        for col in (7,9):
            x=(course+.5)*.243
            y=-.3+(col+.5*(course%2))*.281+.006
            cast('near staggered tile ends; distant continuous plane',[x,y,15],[0,0,-1],
                 'earthen roof tiles' if simplified else 'weathered bargeboard',9)
    import math
    # Measured at the two straight casements cut through the cylindrical return.
    for i in (0,2):
        angle=math.radians(177+(i+.5)*113/3)
        cx,cy=-4.38,1.56
        radial=(math.cos(angle),math.sin(angle))
        for z in (1.81,5.55):
            cast('glazing on rounded wing',[cx+radial[0]*3,cy+radial[1]*3,z],
                 [-radial[0],-radial[1],0],'lead grey glass',3)
    corners=[(3.93,.68),(4.81,-.16),(6.11,.02),(6.86,1.10),(6.68,2.56)]
    for left,right in zip(corners,corners[1:]):
        dx,dy=right[0]-left[0],right[1]-left[1]
        length=math.hypot(dx,dy)
        outward=(dy/length,-dx/length)
        px=(right[0]+left[0])/2+dx/length*.14
        py=(right[1]+left[1])/2+dy/length*.14
        for z in (1.66,5.46):
            cast('sash set into each facet of the canted bay',[px+outward[0],py+outward[1],z],
                 [-outward[0],-outward[1],0],'lead grey glass',2)
        if left!=corners[3]:
            for z,mat in [(4.213,'warm roughcast'),(4.286,'grey moulded stone'),(4.49,'warm roughcast')]:
                cast('two raised borders and recessed field under the upper sash',
                     [px+outward[0],py+outward[1],z],[-outward[0],-outward[1],0],mat,2)
    for course in (4,7,10,13):
        x=course*(.31 if simplified else .243)
        cast('raised lip between the roof tile courses',[x,.83,15],[0,0,-1],'clay tile laps',9)
    for x in (-7.0,7.50):
        cast('outside the studied wings',[x,1,15],[0,0,-1],None,18)
    return dict(triangles=len(mesh.tri),passed=all(r['passed']for r in checks),probes=checks)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--out',type=Path,default=AUDIT/'surface-checks.json')
    args=parser.parse_args()
    bundle=json.loads(args.manifest.read_bytes())
    results={}
    with tempfile.TemporaryDirectory() as tmp:
        for role in ('raw','full','lod'):
            entry=bundle['assets'][role]
            actual=args.manifest.parent/entry['file']
            sha=hashlib.sha256(actual.read_bytes()).hexdigest()
            assert actual.stat().st_size==entry['bytes'] and sha==entry['sha256']
            path=actual
            if role!='raw':
                path=Path(tmp)/(role+'.glb')
                subprocess.run(['node',DECODER,actual,path,PROJECT/'vendor/meshopt_decoder.module.js'],check=True)
            trial=probes(path,role=="lod")
            assert trial['triangles']==entry['triangles']
            results[role]=dict(sha256=sha,**trial)
    ok=all(row['passed'] for row in results.values())
    args.out.write_text(json.dumps(dict(id=ID,passed=ok,variants=results),ensure_ascii=False,indent=2)+'\n')
    assert ok,{k:[r['label']for r in v['probes']if not r['passed']]for k,v in results.items()}


if __name__=='__main__':
    main()
