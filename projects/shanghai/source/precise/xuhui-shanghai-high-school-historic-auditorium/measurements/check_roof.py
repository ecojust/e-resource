"""Trace the roof envelope and separately observable light strip in an exported auditorium."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

ROOT=Path(__file__).absolute().parent
HELPER='data/audit/postal-office-v1/independent-glb-review-helpers.py'
PROJECT=next(p for p in ROOT.parents if (p/HELPER).is_file())
PREFIX='Shanghai High School hall | '

def check(mesh):
    scene=runpy.run_path(str(PROJECT/HELPER))['SerialScene'](mesh)
    d=json.loads((ROOT/'hall-envelope.json').read_bytes())
    z=d['roof_eave_z'];width=d['auditorium_red_roof_half_span']
    ridge=d['roof_pitch_rise'];back=d['stage_cover_z']
    points=[]
    for x in (-13.8,-10.5,-8,-5,-2.1,2.1,5,8,10.5,13.8):
        for y in (10,13,17,21,25,29,34,37):
            if abs(x)>width:
                points.append((x,y,'lateral roof','weathering on flat surfaces',z-.09))
            else:
                points.append((x,y,'central red pitch','weathered red roof covering',z+ridge*(1-abs(x)/width)))
    for y in (40.2,43.4,46.6,49.4,52.7,54.2):
        for x in (-13.8,-8,-3,3,7,9.3,13.8):
            if abs(x)>d['tall_stage_half_width']:
                points.append((x,y,'lateral stage roof','weathering on flat surfaces',z-.065))
            elif x>=5.78:
                points.append((x,y,'pale longitudinal strip','cool grey cast trim',back+.104))
            else:
                points.append((x,y,'upper stage roof','weathering on flat surfaces',back+.045))
    for x in (-13,-9,-4,0,4,9,13):
        for y in (1.3,2.7,4.6):
            points.append((x,y,'entrance head','weathering on flat surfaces',d['south_top_z']-.27))
    rows=[]
    for x,y,zone,surface,height in points:
        hit=scene.ray([x,y,36],[0,0,-1],40)
        ok=bool(hit and hit['material']==PREFIX+surface and abs(hit['point_enu_m'][2]-height)<.017)
        rows.append(dict(x=x,y=y,zone=zone,expected_surface=surface,expected_height_m=height,
                         hit_surface=hit['material'] if hit else None,hit_height_m=hit['point_enu_m'][2] if hit else None,correct=ok))
    # Cast horizontal rays above the red covering and below the old cap:
    # a visually intact crown outline is insufficient to show a seated parapet.
    for x in (-4.8,-2.8,0.,2.8,4.8):
        roof_height=z+ridge*(1-abs(x)/width)
        test_height=roof_height+.195
        hit=scene.ray([x,6.31,test_height],[0.,1.,0.],1.4)
        ok=bool(hit and hit['material']==PREFIX+'ochre render'
                and abs(hit['point_enu_m'][1]-6.99)<.014)
        rows.append(dict(x=x,y=6.31,z=test_height,zone='south face of roof parapet support',
                         expected_y_m=6.99,expected_surface='ochre render',
                         hit_surface=hit['material'] if hit else None,
                         hit_y_m=hit['point_enu_m'][1] if hit else None,correct=ok))
    return dict(mesh=mesh.name,mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),mode='Vertical rays from above and five horizontal rays into the parapet seat. The expected dimensions are the interpreted envelope in hall-envelope.json. The independent evidence and variability are supplied by roof-sources.json.',correct=sum(r['correct'] for r in rows),total=len(rows),samples=rows)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path);args=cli.parse_args()
    report=check(args.mesh);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(report['correct'],report['total'])
    if report['correct']!=report['total']:raise ValueError([r for r in report['samples'] if not r['correct']][:3])
