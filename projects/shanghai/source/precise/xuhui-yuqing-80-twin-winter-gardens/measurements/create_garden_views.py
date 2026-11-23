"""Export the two fitted photo stations and seven model views in local building coordinates."""
from pathlib import Path
import hashlib
import json
import numpy as np
from register_garden import Camera


def photo(number, name, label):
    c=Camera(number)
    forward=c.r[2]
    distance=-c.c[1]/forward[1]
    width,height=c.size
    return dict(name=name,label=label,eye=c.c.tolist(),target=(c.c+distance*forward).tolist(),
                world_up=(-c.r[1]).tolist(),width_m=float(width*distance/c.k[0,0]),
                width=width,height=height,reference=f'Gao {number}')


def manual(name,label,eye,target,width):
    return dict(name=name,label=label,eye=eye,target=target,width_m=width,width=1024,height=680)


def camera_rows():
    return [
        manual('overview','花园立面全景',[-2,-34,8.0],[.0,-.0,4.63],28.2),
        photo(4,'photo-northeast','东北侧摄影机位'),
        photo(6,'photo-southwest','西南侧摄影机位'),
        manual('porch','西南敞廊和白圆柱',[-12.9,-9.1,1.66],[-7.8,-.40,1.60],9.0),
        manual('arch','穿券看木门',[-.40,-3.4,1.55],[-6.67,-.76,1.15],4.95),
        manual('southwest-glass','西南弧窗',[-13.70,-9.6,5.3],[-8.25,-1.15,5.25],8.30),
        manual('central','中廊窗和弯托',[-.45,-12.5,2.15],[.28,-.65,2.25],10.70),
        manual('northeast-glass','东北湾上下层钢窗',[14.30,-12.9,4.25],[8.12,-1.36,3.4],10.75),
        manual('roofline','花园侧上层露台和檐口',[13.7,-21.0,12.1],[2.6,-.15,8.16],19.00),
    ]


if __name__=='__main__':
    out=Path(__file__).resolve().parents[1]/'source/cameras.json'
    rows=camera_rows()
    out.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(hashlib.sha256(out.read_bytes()).hexdigest())
