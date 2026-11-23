"""Inspect the front hips and lower northern roof in the actual export, from above."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
from shapely.geometry import Point, Polygon
HERE=Path(__file__).absolute().parent
HELPER='data/audit/postal-office-v1/independent-glb-review-helpers.py'
PROJECT=next(p for p in HERE.parents if (p/HELPER).is_file())

def check(mesh):
    roof=json.loads((HERE/'roof-extent.json').read_bytes())
    west,east=roof['upper_roof_back_west_east']
    high=Polygon([*roof['front_wall'],east,west]);back=roof['rear_wall_y']
    low=Polygon([west,east,(east[0],back),(west[0],back)])
    scene=runpy.run_path(str(PROJECT/HELPER))['SerialScene'](mesh)
    rows=[];types={'hipped':{'red clay roof tiles','weathered clay hip capping'},'rear':{'pale rear roof'}}
    for zone,plan in [('hipped',high),('rear',low)]:
        interior=plan.buffer(-.48)
        for x10 in range(-60,64,8):
            for y10 in range(0,180,8):
                xy=[x10/10,y10/10]
                if not interior.contains(Point(*xy)):continue
                hit=scene.ray([*xy,18.0],[0.,0.,-1.],15.)
                surface=hit['material'].removeprefix('Fudefang | ') if hit else None
                correct=surface in types[zone]
                if correct and zone=='hipped':correct=11.60<=hit['point_enu_m'][2]<=13.72
                if correct and zone=='rear':correct=10.67<=hit['point_enu_m'][2]<=10.75
                rows.append(dict(xy=xy,zone=zone,hit=surface,z=hit['point_enu_m'][2] if hit else None,correct=bool(correct)))
    return dict(mesh=mesh.name,sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),data='roof-extent.json',
                purpose='Checks exported roof coverage against the authored outline. Dimensions retain the aerial accuracy in roof-extent.json.',
                correct=sum(r['correct'] for r in rows),total=len(rows),samples=rows)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('report',type=Path)
    a=p.parse_args();data=check(a.mesh);a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(data,indent=2)+'\n');print(a.mesh.name,data['correct'],data['total'])
    if data['correct']!=data['total']:raise ValueError([r for r in data['samples'] if not r['correct']][:5])
