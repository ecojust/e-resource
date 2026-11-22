"""Read the actual boundary, brick joints, tablet and strokes in each delivered GLB."""
from pathlib import Path
import os,runpy
from shapely.geometry import Point
from gable import *
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def probe(name,x,z,depth,material):
        h=reader.ray([float(x),-.30,float(z)],[0,1,0],1)
        rows.append(dict(part=name,origin=[float(x),-.30,float(z)],hit=h,material=material,depth_m=depth,passed=bool(h and h['material']==material and abs(h['distance_m']-(.30+depth))<.001)))
    parts_full=dict(fields());parts_lod=dict(fields(True))
    for label,polys in parts_full.items():
        for polygon in sorted(polys,key=lambda q:q.area,reverse=True)[:5]:
            common=polygon.intersection(max(parts_lod[label],key=lambda p:p.intersection(polygon).area))
            if common.is_empty:continue
            pt=common.representative_point();probe(label+' stroke',pt.x,pt.y,-.0135,FADED if label=='童' else INK)
    for x in [-.91,-.67,-.32,0,.31,.66,.91]:
        probe('Blank lower tablet margin',x,BOTTOM+.006,-.012,BOARD);probe('Blank upper tablet margin',x,TOP-.006,-.012,BOARD)
    for x in [-1.12,-.8,-.44,0,.52,.85,1.11]:
        probe('Exposed face brick below',x,.10,.025,BRICK);probe('Exposed face brick above',x,.712,.025,BRICK)
        probe('Horizontal bedding joint',x,.075,.048,BASE)
    for z in [.10,.712]:probe('Exposed vertical brick joint',.82,z,.048,BASE)
    for side in [-1,1]:probe('Narrow outer edge',side*1.005,.37,.009,EDGE)
    return dict(passed=all(x['passed'] for x in rows),samples=rows)
