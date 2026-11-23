"""Trace fixed native Fayhoo photo points through a decoded GLB, including the open grille."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import runpy
import sys

import numpy as np
from register_front import Camera

HERE=Path(__file__).resolve().parent
sys.path.append(str(HERE.parent/'source'))
from street_entry import GREEN, ENAMEL, WHITE, STONE, DARK, STEEL, GLASS, CALL, INSERT

# Native 2144x1424. The green frame, pale arch and dark space behind the bars
# must remain different surfaces when the surrounding masonry is assembled.
SAMPLES=[
    ('upper trapezoidal key',(1196,1023),STONE),
    ('shallow arch at crown',(1193,1052),STONE),
    ('shallow arch east side',(1246,1084),STONE),
    ('overlight head',(1200,1037),GREEN),
    ('west overlight rod',(1146,1055),GREEN),
    ('central overlight rod',(1197,1053),GREEN),
    ('east overlight rod',(1241,1057),GREEN),
    ('main transom',(1185,1073),GREEN),
    ('clear arch below top',(1202,1067),DARK),
    ('upper east main rod',(1227,1107),GREEN),
    ('between upper rods',(1229.5,1107),DARK),
    ('lower centre rod',(1199,1221),GREEN),
    ('lower open slot',(1201.5,1221),DARK),
    ('upper waist bar',(1179,1152),GREEN),
    ('between waist bars',(1179,1154),DARK),
    ('low waist bar',(1178,1186),GREEN),
    ('east lock panel',(1232,1172),GREEN),
    ('pale intercom edge',(1244,1125),CALL),
    ('dark upper intercom grille',(1249,1123),INSERT),
    ('intercom display',(1248,1129),INSERT),
    ('west number green field',(1105,1093),ENAMEL),
    ('west 2 curved head',(1112.0,1091.45),WHITE),
    ('west 2 base',(1112,1098.2),WHITE),
    ('east number green field',(1835.5,1072.5),ENAMEL),
    ('east 2 base',(1842,1077.6),WHITE),
    ('east end window head',(1773,966),STONE),
    ('east end window sill',(1780,1073),STONE),
    ('east end window low left pane',(1751,1055),GLASS),
    ('east end window low right pane',(1776,1054),GLASS),
    ('east end window middle left pane',(1748,1026),GLASS),
    ('east end window low mullion',(1762.4,1052),STEEL),
    ('east end window middle transom',(1772,1017.3),STEEL),
]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path);p.add_argument('report',type=Path)
    p.add_argument('--scale',nargs=3,type=float,default=(1.,1.,1.),metavar=('SX','SY','SZ'))
    args=p.parse_args()
    scene=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'](args.mesh)
    c=Camera();scale=np.asarray(args.scale);rows=[]
    for name,point,expected in SAMPLES:
        hit=scene.ray(c.c*scale,c.ray(point)*scale,75)
        rows.append(dict(feature=name,native_pixel=point,expected=expected,actual=hit,passed=bool(hit and hit['material']==expected)))
    out=dict(mesh=args.mesh.name,mesh_sha256=sha256(args.mesh.read_bytes()).hexdigest(),
             camera_sha256=sha256((HERE/'2015-street-camera.json').read_bytes()).hexdigest(),
             source_image_sha256='de0b409edfd8501a759396472b73308bf1d0521a96906d655a4fd0c812aac263',
             photographic_dimensions=[2144,1424],scale=args.scale,passed=sum(r['passed'] for r in rows),total=len(rows),rows=rows)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(out['passed'],out['total'],[(r['feature'],(r['actual'] or {}).get('material')) for r in rows if not r['passed']])

if __name__=='__main__':
    main()
