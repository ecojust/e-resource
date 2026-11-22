"""Check brick courses and sash members by casting rays into the actual GLB."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from math import acos, cos, pi, sin, sqrt
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene

TIMBER = 'Shanyin sash | pale painted timber'
RAILS = 'Shanyin sash | meeting rails'
GLASS = 'Shanyin sash | slightly blue glass'
LOWER = 'Shanyin sash | grey lower glass'
BED = 'Shanyin arch | warm pointing'
LEDGE = 'Shanyin arch | moulded springing'
BRICK = ('Shanyin arch | red facing', 'Shanyin arch | amber red', 'Shanyin arch | dark red')


def observations(rows):
    for i, row in enumerate(rows):
        x0, x1 = row['x0'], row['x1']
        w, centre = x1-x0, (x1+x0)/2
        spring, sill = row['z_spring'], row['z_sill']
        rise = row['z_crown']-spring
        ring = row['brick_ring']
        radius = (.25*w*w+rise*rise)/(2*rise)
        cz = row['z_crown']-radius
        y = row.get('face_y', 0)
        glass_depth = row.get('recess', .063*w)+.048*w

        def point(label, x, z, materials, depth):
            return dict(opening=row.get('id', i+1), feature=label, x=x, z=z,
                        origin_y=y-.30*w, width=w, materials=materials, depth=y+depth)

        for label, x, z in [('left jamb', x0+.008*w, (spring+sill)/2),
                            ('right jamb', x1-.008*w, (spring+sill)/2),
                            ('sill rail', centre-.18*w, sill+.008*w),
                            ('curved outer casing', centre, row['z_crown']-.008*w)]:
            yield point(label,x,z,[TIMBER],row.get('recess', .063*w))
        cuts = ((.257,.524,.754),(.242,.458,.766),(.245,.492,.746))[i]
        for f in cuts:
            yield point('lower upright',x0+f*w,sill+.44*(spring-sill),[RAILS],glass_depth-.043*w)
        for p, q in zip((0,*cuts), (*cuts,1)):
            yield point('lower pane', x0+(p+q)*w/2,sill+.50*(spring-sill),[LOWER],glass_depth)
        yield point('spring transom', centre+.22*w,spring,[RAILS],glass_depth-.043*w)
        yield point('small inner arch',centre,spring+.087*w,[RAILS],glass_depth-.043*w)
        yield point('inner fanlight pane',centre,spring+.047*w,[GLASS],glass_depth)
        for angle in (45.7,90,134.6):
            a=angle*pi/180
            yield point('fanlight spoke',centre+.17*w*cos(a),spring+.17*w*sin(a),[RAILS],glass_depth-.043*w)
        for angle in (21,68,112,159):
            a=angle*pi/180
            yield point('outer fanlight pane',centre+.19*w*cos(a),spring+.19*w*sin(a),[GLASS],glass_depth)
        for edge, direction in ((x0,-1),(x1,1)):
            for fraction, depth in ((-.095,-.032),(-.055,-.047),(-.018,-.059)):
                yield point('impost step', edge+direction*.081*w,spring+fraction*w,[LEDGE],depth*w)

        # Three narrow annular joints remain visible between the four concentric courses.
        # Use off-axis points so the two bands at the top are also tested on either side.
        for b in (.39,.70,.85):
            for deg in (67,89,113):
                a=deg*pi/180
                yield point('curved mortar joint',centre+(radius+b*ring)*cos(a),
                            cz+(radius+b*ring)*sin(a),[BED],-.014*w)
        for j, band in enumerate((.195,.545,.775,.925),1):
            for deg in (63.7,74.9,86.2,95.4,106.6,115.1):
                a=pi*deg/180
                # Occasional radial joints legitimately pass through an angular sample.
                # Count facing bricks separately per course after the intersection.
                yield point(f'brick course {j}',centre+(radius+band*ring)*cos(a),
                            cz+(radius+band*ring)*sin(a),[*BRICK,BED],-.022*w)


def inspect(model, rows):
    scene=SerialScene(model)
    records=[]
    for p in observations(rows):
        hit=scene.ray((p['x'],p['origin_y'],p['z']),[0,1,0],p['width'])
        mat=hit['material'] if hit else None
        depth=hit['point_enu_m'][1] if hit else None
        tolerance=.010*p['width'] if p['feature'].startswith('brick course') else .0018*p['width']
        ok=mat in p['materials'] and abs(depth-p['depth'])<=tolerance
        records.append(dict(opening=p['opening'],feature=p['feature'],x=round(p['x'],5),
                            z=round(p['z'],5),actual_material=mat,actual_y=round(depth,6) if hit else None,
                            expected_y=round(p['depth'],6),passed=bool(ok)))
    face_checks=[]
    for i,r in enumerate(rows):
        for j in range(1,5):
            sel=[k for k in records if k['opening']==r.get('id',i+1) and k['feature']==f'brick course {j}']
            faces=sum(k['actual_material'] in BRICK for k in sel)
            face_checks.append(dict(opening=r.get('id',i+1),course=j,brick_hits=faces,samples=len(sel),passed=faces>=4))
    return dict(model_sha256=scene.asset['sha256'],model_bytes=scene.asset['bytes'],rays=len(records),
                matched=sum(v['passed'] for v in records),facing_samples=face_checks,probes=records,
                passed=all(v['passed'] for v in [*records,*face_checks]))


def photo_error(layout):
    P=np.asarray(layout['camera_P'])
    photo=json.loads((HERE/'three-fanlight-photograph.json').read_bytes())['left_to_right'][1]
    row=layout['rows'][1];w=row['x1']-row['x0'];rise=row['z_crown']-row['z_spring']
    radius=(w*w/4+rise*rise)/(2*rise)
    centre=(row['x0']+row['x1'])/2;cy=row['z_crown']-radius
    a=acos(w/(2*radius))
    theta=np.linspace(a,pi-a,1001)
    points=np.vstack([centre+radius*np.cos(theta),np.full(len(theta),row.get('face_y',0)),
                      cy+radius*np.sin(theta),np.ones(len(theta))])
    uv=P@points;curve=(uv[:2]/uv[2]).T
    dist=[float(np.linalg.norm(curve-np.asarray(pt),axis=1).min()) for pt in photo['clear_arc_pixels']]
    return dict(points=len(dist),distances_px=dist,rms_px=float(np.sqrt(np.mean(np.square(dist)))),
                method='Native photograph samples to the projected nominal middle opening looking at the wall plane.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('layout',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('models',nargs='+',type=Path)
    args=parser.parse_args()
    layout=json.loads(args.layout.read_bytes())
    rows=[inspect(p,layout['rows']) for p in args.models]
    result=dict(layout_sha256=sha256(args.layout.read_bytes()).hexdigest(),assets=rows)
    if 'camera_P' in layout:
        result['photograph']=photo_error(layout)
    args.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    for r in rows:
        print(r['matched'],r['rays'],[(v['opening'],v['feature'],v['actual_material']) for v in r['probes']if not v['passed']][:10],r['passed'])
    raise SystemExit(any(not r['passed'] for r in rows))
