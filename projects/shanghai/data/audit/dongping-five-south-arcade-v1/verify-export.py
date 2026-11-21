"""Check the three lower arches, five upper lights, turned rails, drainpipes, front treads and dormer."""
from pathlib import Path
from math import cos, pi, sin
import argparse
import json
import runpy

HERE=Path(__file__).resolve().parent
trace=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']


def cases():
    from math import sqrt
    dims=json.loads((HERE.parents[2]/'source/precise/xuhui-dongping-five-south-arcade/measurements/south-elevation-ratios.json').read_bytes())
    q=dims['direct_readings'];scale=dims['metres_per_pixel']
    X=lambda px:(px-q['centre_x'])*scale
    Z=lambda py:(q['grade_y']-py)*scale
    walls=json.loads((HERE.parents[2]/'source/precise/xuhui-dongping-five-south-arcade/measurements/rear-gallery-readings.json').read_bytes())
    tests=[]
    def ray(name,origin,direction,mat=None,depth=None):
        tests.append(dict(name=name,origin=list(origin),direction=list(direction),length=5.5,
                          allowed=[mat]if isinstance(mat,str)else mat,range_m=depth))
    def front(name,x,z,mat=None,depth=None):
        if mat=='Recessed gallery plaster':
            # Existing clear-opening rays must pass through the facade and reach the photographed back wall.
            # A rear dark field sits further away than an intact pier or timber reveal.
            for level,objects in walls['visible_fields'].items():
                for field in objects:
                    left,right=[X(pos) for pos in field['limits']]
                    sill,head=Z(walls[level+'_sill_y']),Z(field['head'])
                    if left<x<right and sill<z<head:
                        if min(x-left,right-x)<.036 or head-z<.044:
                            mat='Shaded inner masonry'
                        else:
                            mat='Blue-black gallery recesses'
                            depth=[3.895,3.925]
        ray(name,(x,-1.60,z),(0,1,0),mat,depth)
    for level,centres,widths,spring in [('Ground',q['lower_centres_x'],q['lower_openings_px'],Z(q['lower_spring_y'])),
                                        ('Upper',q['upper_centres_x'],q['upper_diameters_px'],Z(q['upper_spring_y']))]:
        for i,(c,diameter)in enumerate(zip(centres,widths),1):
            cx,r=X(c),diameter*scale/2
            for fraction in (-.68,0,.68):
                xx=cx+fraction*r
                rise=r*sqrt(1-fraction*fraction)
                front(f'{level} {i}, clear below round crown at {fraction}',xx,spring+rise-.085,
                      'Recessed gallery plaster',[3.735,3.765])
                front(f'{level} {i}, solid above round crown at {fraction}',xx,spring+rise+.085,
                      'Grey pebble render',[1.595,1.605])
    for i,c in enumerate(q['upper_centres_x'],1):
        cx=X(c);span=q['upper_diameters_px'][i-1]*scale
        foot=Z(q['railing_foot_y']);top=Z(q['railing_top_y'])
        front(f'Upper {i} carved spindle in centre',cx,(foot+top)/2,'Warm white balusters',[1.47,1.54])
        front(f'Upper {i} daylight beside spindle',cx+span/14,(foot+top)/2,'Recessed gallery plaster',[3.735,3.765])
        front(f'Upper {i} handrail',cx+.12,top-.05,'Warm white balusters',[1.44,1.46])
    for px in (532.5,609.5,686.5,763.5):
        front(f'Tapered gallery column at {px}',X(px),Z(289),'Warm white balusters',[1.51,1.72])
    for i in (0,2):
        cx=X(q['lower_centres_x'][i]);span=q['lower_openings_px'][i]*scale
        h=(Z(q['porch_floor_y'])+Z(470))/2
        front(f'Lower rail {i} spindle',cx+span*.05,h,'Warm white balusters',[1.47,1.54])
        front(f'Lower rail {i} open centre',cx,h,'Recessed gallery plaster',[3.735,3.765])
    for u in (-.64,0,.64):
        front(f'Central opening behind access steps {u}',X(649)+u,1.63,'Recessed gallery plaster',[3.735,3.765])
    for i in range(4):
        expected=2-Z(q['porch_floor_y'])*(4-i)/4
        ray(f'Red tread level {i+1}',(X(649),-.11-i*.30,2),(0,0,-1),'Red quarry steps',[expected-.006,expected+.006])
    for px in (440,851):
        for height in (1.72,3.65,5.95):
            front(f'Downpipe {px} at {height}',X(px),height,'Cast iron rainwater goods',[1.43,1.48])
    for px in (420,578,716,864):
        front(f'Ground pier at x {px}',X(px),1.87,'Grey pebble render',[1.59,1.61])
    for xx in (-.227,.227):
        front(f'Dormer shutter meeting stile {xx}',X(633)+xx,Z(177),'Dark timber and eaves',[2.59,2.67])
    for u in (X(398)-.36,X(871)+.36):
        front('Open air outside elevation '+str(round(u,3)),u,4.0)
    # In the original photo these alternating light and dark midpoints remain visible despite the deep shade.
    # Set origins behind the front rails so the tested surfaces belong to the second wall.
    for yy, dark, light in [(447,(474,509,552,606,662,749,805),(489,538,635,780)),
                            (294,(477,504,567,640,709,746,795),(589,667,727,817))]:
        for xx in dark:
            ray(f'Photographed rear field at ({xx},{yy})',(X(xx),.65,Z(yy)),(0,1,0),'Blue-black gallery recesses',[1.65,1.67])
        for xx in light:
            ray(f'Photographed rear pier at ({xx},{yy})',(X(xx),.65,Z(yy)),(0,1,0),'Recessed gallery plaster',[1.49,1.51])
    ray('Sight up to the upper gallery roof soffit',(0,.75,Z(270)),(0,0,1),'Shaded inner masonry',[Z(235)-Z(270)-.01,Z(235)-Z(270)+.01])
    return tests


def terrace_seams(path):
    """Each exposed tread, landing and coping has one finish at the common floor elevation."""
    scene_class = runpy.run_path(HERE.parent/'postal-office-v1/independent-glb-review-helpers.py')['SerialScene']
    scene=scene_class(path)
    dims=json.loads((HERE.parents[2]/'source/precise/xuhui-dongping-five-south-arcade/measurements/south-elevation-ratios.json').read_bytes())
    floor=(dims['direct_readings']['grade_y']-dims['direct_readings']['porch_floor_y'])*dims['metres_per_pixel']
    results=[]
    for x,y,finish in [(-1.54,-.18,'Red quarry steps'),(1.54,-.12,'Red quarry steps'),
                       (-1.04,-.06,'Red quarry steps'),(.15,-.06,'Red quarry steps'),
                       (1.03,-.021,'Red quarry steps'),(-1.02,.031,'Cream rail ledges'),
                       (.11,.030,'Cream rail ledges'),(1.02,.16,'Cream rail ledges'),
                       (.26,.23,'Cream rail ledges')]:
        surfaces=[]
        for material in ['Red quarry steps','Cream rail ledges','Grey pebble render']:
            hit=scene.ray((x,y,floor+.045),(0,0,-1),.055,lambda name:name==material)
            if hit is not None:
                surfaces.append(material)
        results.append(dict(position=[x,y,floor],finishes=surfaces,expected=finish,passed=surfaces==[finish]))
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('raw','full','lod','output'):
        parser.add_argument(key,type=Path)
    args=parser.parse_args()
    result={role:trace(getattr(args,role),cases())for role in ('raw','full','lod')}
    for role,row in result.items():
        row['terrace_seams']=terrace_seams(getattr(args,role))
        row['passed'] = row['passed'] and all(v['passed'] for v in row['terrace_seams'])
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    for role,row in result.items():
        print(role,len(row['cases']),[(v['name'],v['first_hit']) for v in row['cases']if not v['passed']],flush=True)
    raise SystemExit(not all(row['passed']for row in result.values()))
