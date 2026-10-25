"""Blender geometric ray tests: demonstrate actual wall openings, not painted panes.

blender -b --python verify_recesses.py
"""
from pathlib import Path
import argparse, json, os, sys
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--models',type=Path,default=Path(os.environ.get('CLASSICAL_BANK_OUTPUT_DIR',str(ROOT))))
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
MODELS=args.models.resolve()
data=json.loads((ROOT/'geometry-input.json').read_text())
results=[]
for name,key in [('hsbc','bund12'),('russo','bund15')]:
    bpy.ops.wm.open_mainfile(filepath=str(MODELS/name/(name+'.blend')))
    obj=next(o for o in bpy.data.objects if o.get('true_recessed_window_count'))
    d=data[key];u=d['world_basis_u'];v=d['world_basis_v'];cx,cy=d['front_center']
    def cast(x,z):
        px,py=cx+x,cy-4
        start=Vector((u[0]*px+v[0]*py,u[1]*px+v[1]*py,z))
        direction=Vector((v[0],v[1],0))
        hit,location,normal,index=obj.ray_cast(start,direction,distance=15)
        if not hit:raise AssertionError((name,x,z,'no hit'))
        return (location-start).dot(direction),obj.data.polygons[index].material_index
    if name=='hsbc':
        wing=(d['front_width']-25.4)/2/7;wx=12.7+wing/2
        distance,material=cast(wx,10.3);wall_distance,_=cast(wx+wing*.46,10.3);expected=4.57
    else:
        distance,material=cast(0,8.0);wall_distance,_=cast(16,2.0);expected=4.89
    assert abs(distance-expected)<.025,(name,distance,expected)
    assert distance-wall_distance>.50,(name,distance,wall_distance)
    assert abs(min(v.co.z for v in obj.data.vertices))<1e-5
    results.append({'id':name,'window_hit_distance_m':distance,'expected_distance_m':expected,
                    'wall_hit_distance_m':wall_distance,'verified_recess_m':distance-wall_distance,
                    'window_count':obj['true_recessed_window_count'],'passed':True})
(MODELS/'geometry-verification.json').write_text(json.dumps({'complete':True,'tests':results},indent=2))
print(json.dumps(results))
