"""Intersect fixed original-image pixels with each actual decoded courtyard mesh."""
from pathlib import Path
import argparse
import hashlib
import json
from check_large_window import SerialScene
from register_courtyard import Camera
from plan_points import load as read_plan
import numpy as np


HERE=Path(__file__).resolve().parent
PICKS=[
    ('wave sheet, left half',(102,125),['corrugated sheet']),
    ('wave sheet, right half',(216,125),['corrugated sheet']),
    ('wave sheet, left upper lip',(95,120),['corrugated sheet']),
    ('thick front rail post',(114,233),['dark grey balcony steel']),
    ('light middle rail',(135,222),['light painted diagonal rail']),
    ('light rising brace',(97,215),['light painted diagonal rail']),
    ('light crossing brace',(125,232),['light painted diagonal rail']),
    ('front fascia at centre',(153,246),['dark grey balcony steel','grey balcony deck']),
    ('visible underside',(206,252),['grey balcony deck']),
    ('two underside wall supports, left',(144,265),['grey balcony deck']),
    ('two underside wall supports, right',(236,263),['grey balcony deck']),
    ('rose skirt, left',(240,293),['faded rose awning']),
    ('rose skirt, middle',(282,293),['faded rose awning']),
    ('rose skirt, right',(346,294),['faded rose awning']),
    ('upper left fan',(120,85),['recessed fan screen','galvanized support angles']),
    ('upper middle fan',(250,85),['recessed fan screen','galvanized support angles']),
    ('upper middle case',(268,83),['pale equipment housing']),
    ('narrow window fan',(296,215),['recessed fan screen','galvanized support angles']),
    ('narrow window case',(314,211),['pale equipment housing']),
    ('lower fan',(269,249),['recessed fan screen','galvanized support angles']),
    ('lower case',(287,246),['pale equipment housing']),
]
def inspect(path,local=False):
    scene=SerialScene(path);c=Camera('case1');rows=[]
    pose=np.eye(4) if local else np.asarray(read_plan()['facade_frames']['case1']['local_to_ENU'])
    eye=(pose@[*c.c,1])[:3]
    for label,pixel,materials in PICKS:
        hit=scene.ray(eye,pose[:3,:3]@c.ray(pixel),45.)
        rows.append(dict(feature=label,pixel=pixel,expected=materials,first_hit=hit,
                         passed=bool(hit and any(m in hit['material']for m in materials))))
    return dict(source_image_sha256='7ad4ed0d72a12e59155b97b88f7a71fe21dce7599e34c5cfa8ef49d899c9997c',
                camera_sha256=hashlib.sha256((HERE/'courtyard-cameras.json').read_bytes()).hexdigest(),
                asset=scene.asset,total=len(rows),direct=sum(r['passed']for r in rows),measurements=rows)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--local',action='store_true');cli.add_argument('asset',type=Path);cli.add_argument('report',type=Path)
    args=cli.parse_args();report=inspect(args.asset,args.local);args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(report['direct'],report['total'],[(r['feature'],r['first_hit']['material']if r['first_hit']else None)for r in report['measurements']if not r['passed']])
