"""Compose six architectural views and carry three registered photographic stations into the model."""
import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).absolute().parent

def view(name, label, eye, target, width_m, width=1000, height=720):
    return dict(name=name, label=label, eye=eye, target=target, width_m=width_m,
                width=width, height=height)


def photo(station, label):
    record=json.loads((HERE/'court-cameras.json').read_bytes())['views'][station]
    r=np.array(record['R']);c=np.array(record['C'])
    depth=(.80-c[1])/r[2,1]
    target=c+depth*r[2]
    w,h=record['size']
    fx,fy=record['K'][0][0],record['K'][1][1]
    v=view('photo-'+station,label,c.tolist(),target.tolist(),float(w*depth/fx),w,h)
    v.update(reference='Gao '+station,world_up=(-r[1]).tolist(),pixel_aspect_y=fx/fy)
    return v


def cameras():
    return [
        view('overview','庭院正面与西侧全景',[-15.,-36.,12.2],[0.,3.9,6.15],25.6,1000,740),
        photo('03','两翼与门廊正照原机位'),
        photo('04','2013年西侧原机位'),
        photo('05','弧形台阶斜照原机位'),
        view('columns','四柱与弧形阳台',[-4.5,-11.,4.75],[0.,.35,3.98],9.0),
        view('upper','直阳台、栏板与檐口',[2.5,-12.4,9.5],[0.,.6,8.20],8.8),
        view('carving','切角窗与窗裙雕饰',[.2,-8.9,5.55],[-4.0,.25,5.96],4.65),
        view('west','西墙百叶、砖雕与落水管',[-16.0,-3.8,8.00],[-6.43,3.42,7.14],6.3),
        view('entry','门厅、弧阶与地面镶花',[1.45,-6.8,2.0],[0.,.88,1.62],5.9),
    ]


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    args.output.write_text(json.dumps(cameras(),ensure_ascii=False,indent=2)+'\n')
