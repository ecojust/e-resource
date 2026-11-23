"""Measure the distance from the brick face to the floor edge in two exterior wall sections."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if (p / 'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

def check(path):
    scene = SerialScene(path)
    layout = json.loads((HERE.parent / 'source/courtyard-layout.json').read_bytes())
    corners = np.asarray(layout['outer_corners'])
    rows = []
    for face, axis in [(0, 7.11), (3, 24.27)]:
        a,b = corners[face],corners[(face+1)%4]
        tangent = (b-a)/np.linalg.norm(b-a)
        inward = np.array([-tangent[1],tangent[0],0.])
        origin_xy = a + tangent * axis - inward[:2]*0.6
        for level in range(1,6):
            z=level*layout['storey_pitch']-layout['slab_thickness']*.5
            start=np.r_[origin_xy,z]
            brick=scene.ray(start,inward,1.1,lambda m:m=='Court | red brick')
            deck=scene.ray(start,inward,1.1,lambda m:m=='Court | floor concrete')
            first=scene.ray(start,inward,1.1)
            assert brick and deck and first
            gap=deck['distance_m']-brick['distance_m']
            rows.append({'face':['west','south','east','north'][face],'axis_m':axis,'level':level,
                         'origin':start.tolist(),'inward':inward.tolist(),'exposed_material':first['material'],
                         'brick_distance_m':brick['distance_m'],'floor_distance_m':deck['distance_m'],
                         'recess_m':gap})
    return {'mesh':scene.asset,'sections':rows}

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('output',type=Path)
    cli.add_argument('--before',type=Path,required=True)
    cli.add_argument('current',nargs='+',type=Path)
    args=cli.parse_args()
    former=check(args.before)
    revised=[check(path) for path in args.current]
    assert all(abs(row['recess_m'])<.00002 for row in former['sections'])
    assert all(abs(row['recess_m']-.12)<.00002 for item in revised for row in item['sections'])
    result={'previous':former,'revised':revised,'previous_publication':'6822ebb453217ad97008b61cc81519f7c76b3a20'}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
