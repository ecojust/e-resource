"""Native portrait or landscape pixels to the common X/north, Y/inward, Z/up building frame."""
import json
from pathlib import Path

import numpy as np

_RECORD=json.loads((Path(__file__).resolve().parents[1]/'measurements/east-front-cameras.json').read_bytes())
CAMERAS={key:np.array(_RECORD[key]['matrix']) for key in ('2014_oblique','2016_front')}


def on_wall(u,v,y=0.,camera='2014_oblique'):
    """Intersect the image ray with a plane parallel to the main east frontage."""
    m=CAMERAS[camera];eye=-np.linalg.solve(m[:,:3],m[:,3]);d=np.linalg.solve(m[:,:3],[u,v,1.])
    return eye+(y-eye[1])*d/d[1]


def pixel(xyz,camera='2014_oblique'):
    m=CAMERAS[camera];p=m[:,:3]@np.asarray(xyz)+m[:,3]
    return p[:2]/p[2]
