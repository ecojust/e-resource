"""Render the 2017 audience/gallery view from its conditional hallway camera on the reopened glTF."""
import argparse
import json
from pathlib import Path
from render_vestibule import render_indoor
HERE=Path(__file__).resolve().parent
def render(mesh,out,pixels=850):
    registration=json.loads((HERE/'auditorium-station.json').read_bytes())
    w,h=registration['frame']
    proof=render_indoor(mesh,out,registration,(0,0,w,h),pixels)
    proof['camera']='approximate 2017 indoor view fitted to the longitudinal aisle, door, gallery and side windows'
    return proof
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('out',type=Path);ap.add_argument('--width',type=int,default=850);a=ap.parse_args()
    print(json.dumps(render(a.mesh,a.out,a.width),ensure_ascii=False))
