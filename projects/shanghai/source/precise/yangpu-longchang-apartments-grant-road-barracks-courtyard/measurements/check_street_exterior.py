"""Cast unfiltered first-hit rays on the actual raw and independently decoded web assets."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Polygon

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'source'
PROJECT = next(parent for parent in HERE.parents if (parent / 'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(PROJECT / 'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

GLASS = 'Street | grey daylight glazing'
BRICK = 'Court | red brick'
STEEL = 'Street | painted iron casements'


def exterior_controls():
    fabric = json.loads((SOURCE/'street-fabric.json').read_bytes())
    layout = json.loads((SOURCE/'courtyard-layout.json').read_bytes())
    corners = np.array(layout['outer_corners'])
    storey = layout['storey_pitch']
    rays = []

    def sample(label, group, point, inward, material, expected, tolerance=.03, length=2):
        rays.append((label,group,np.asarray(point),np.asarray(inward),material,expected,tolerance,length))

    for ix, name in enumerate(['west','south','east','north']):
        start, end = corners[ix], corners[(ix+1)%4]
        tangent = (end-start)/np.linalg.norm(end-start)
        inward = np.array([-tangent[1],tangent[0]])
        direction = [*inward,0.]
        def at(s,d,z):
            return [*(start+s*tangent+d*inward),z]
        entries = fabric[name]
        for axis in entries['axes']:
            for level in axis['levels']:
                settings = axis | axis.get('overrides', {}).get(str(level), {})
                width = settings['width']
                bottom = level*storey+settings['sill']
                height = settings['height']
                tag = f"{axis['id']}-floor-{level+1}"
                # The recess test begins behind the steel cage, but before the
                # glazing; the jamb and sill tests use rays from the street.
                sample(tag+' glass','glass inset',at(axis['x']+.109*width,.070,bottom+height*.59),direction,GLASS,.089,.012)
                sample(tag+' sill','sill',at(axis['x']-.214*width,-.8,bottom-.042),direction,'Street | sill stone',.621,.023)
                sample(tag+' outer brick','masonry flanks',at(axis['x']+width/2+.265,-.018,bottom+.61*height),direction,BRICK,.018,.016)
            if axis['id']=='W01':
                sample('solid third-floor northmost street bay','photographed blind bay',at(axis['x'],-.08,2*storey+1.61),direction,BRICK,.08)
        sample(name+' cornice','outer cornices',at(np.linalg.norm(end-start)*.69,-.60,5*storey+1.59),direction,'Street | warm pale cornice',.45,.04)
    for roof in fabric['north_roof_projections']:
        poly=Polygon(roof['outline_xy'])
        centre=poly.centroid
        target=5*storey+roof['top_above_roof_deck']+.12
        sample(roof['id'],'two north roof boxes',[centre.x,centre.y,target+2.0],[0,0,-1],'Court | washed aggregate',2.0,.02,4)
    return rays


def inspect(path, controls):
    scene = SerialScene(path)
    failures=[]
    all_rows=[]
    groups={}
    for name, group, origin, direction, material, expected, tolerance, length in controls:
        hit=scene.ray(origin,direction,length)
        passed=bool(hit and hit['material']==material and abs(expected-hit['distance_m'])<=tolerance)
        rows=groups.setdefault(group,[0,0])
        rows[0]+=int(passed)
        rows[1]+=1
        entry={'name':name,'matched':passed,'origin':np.round(origin,5).tolist(),'direction':np.round(direction,6).tolist(),'wanted':material,'expected_distance_m':round(expected,5),'tolerance_m':round(tolerance,5),'actual':hit}
        all_rows.append(entry)
        if not passed:
            failures.append(entry)
    return {'asset':scene.asset,'groups_hit_total':groups,'failed':failures,'records':all_rows}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['raw','full','lod']:
        ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    controls=exterior_controls()
    result={role:inspect(getattr(args,role),controls) for role in ['raw','full','lod']}
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,check in result.items():
        print(role,check['groups_hit_total'])
