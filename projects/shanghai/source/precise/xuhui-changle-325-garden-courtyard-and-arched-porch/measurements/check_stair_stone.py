"""Read the actual GLB surfaces in the original courtyard photograph's pixel coordinates."""
import argparse
import json
from pathlib import Path
import sys
from register_court import Camera
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
STONE='325 porch | mottled grey stair stone';EDGE='325 porch | worn pale tread edge'
RAIL='325 porch | sandy carved balustrade stone';TOP='325 porch | weathered handrail top'
RENDER='325 garden | pale ochre pebble finish';BASE='325 porch | darker grey plinth course'
SAMPLES=[
    ('exposed riser',[(474,1073),(529,1050),(581,1029),(625,1014),(653,994),(674,977),(711,954),(741,939),(755,919)],{STONE}),
    ('pale nosing',[(535,1080),(585,1059),(620,1038),(678,1018),(700,999),(642,980),(533,961),(559,945),(614,926),(634,908)],{EDGE,STONE}),
    ('two lower dishes',[(379,859),(839,858),(376,875),(839,875)],{TOP}),
    ('two top finials',[(468,775),(885,775)],{RAIL}),
    ('lower newel shafts',[(376,945),(843,947)],{RAIL}),
    ('sloping upper handrail',[(407,875),(436,838),(461,800),(857,852)],{TOP}),
    ('front plaster',[(487,780),(491,870),(544,677),(810,674),(860,751)],{RENDER}),
    ('stone at jamb foot',[(495,899),(858,900)],{BASE}),
]
def read(path):
    scene=SerialScene(path);camera=Camera('fayhoo');rows=[]
    for label,points,expect in SAMPLES:
        for u,v in points:
            h=scene.ray(camera.c,camera.ray((u,v)),60)
            rows.append(dict(feature=label,original_pixel=[u,v],expected=sorted(expect),
                             actual=h,match=bool(h and h['material']in expect)))
    return dict(camera='fayhoo',asset=scene.asset,observations=rows,
                matched=sum(r['match']for r in rows),total=len(rows))
if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    a=cli.parse_args();r=read(a.mesh);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['matched'],r['total'],[(v['feature'],v['original_pixel'],v['actual']['material']if v['actual']else None)for v in r['observations']if not v['match']])
