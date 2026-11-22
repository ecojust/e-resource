"""Two raised yellow wordmark lines at the river end of Guangfu Road 195's east wall."""
from pathlib import Path
import json

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union
from south_entrance import finish, LETTERS

HERE=Path(__file__).resolve().parents[1]/'measurements'
GOLD='East return | illuminated yellow face'
SIDE='East return | dark brass letter returns'
PALETTE={GOLD:finish([227,187,89],.41,.40),SIDE:finish([101,77,45],.58,.37)}


def shaped_rows(measurements=HERE):
    data=json.loads((measurements/'east-return-word-shapes.json').read_bytes())
    donor={item['text']:item for item in LETTERS}
    rows=[]
    for record in data['top']:
        name=record['text'];shape=unary_union([Polygon(p['outer'],p['holes']) for p in donor[name]['polygons']])
        # The frontal artwork reads downwards in image v; return-wall height increases upwards.
        shape=affinity.scale(shape,xfact=1,yfact=-1,origin=(0,0))
        a,b,c,d=shape.bounds;left,foot,right,top=record['bbox_s0_z0_s1_z1']
        shape=affinity.translate(shape,-a,-b)
        shape=affinity.scale(shape,xfact=(right-left)/(c-a),yfact=(top-foot)/(d-b),origin=(0,0))
        rows.append(('Upper',name,affinity.translate(shape,left,foot)))
    for record in data['bottom']:
        rows.append(('Lower',record['text'],unary_union([Polygon(p[0],p[1:])for p in record['polygons']])))
    return rows


def map_to_wall(layout,measurements=HERE):
    reg=json.loads((measurements/'east-return-sign-registration.json').read_bytes())
    origin,end=np.asarray(layout['east_return'],float)
    delta=end-origin;length=np.linalg.norm(delta);along=delta/length
    normal=np.array([along[1],-along[0]])
    def mapper(s,z,d):
        xy=origin+along*s*(length/reg['east_return_length_m'])+normal*d
        return (xy[0],xy[1],z+layout['bay_wall_top']-reg['bay_wall_top_m'])
    return mapper,normal


def add_east_wall_sign(b,lod=False,layout=None):
    if layout is None:layout=json.loads((HERE/'riverfront-layout.json').read_bytes())
    low=lod is True or lod=='lod';face,_=map_to_wall(layout)
    for i,(row,name,shape) in enumerate(shaped_rows(),1):
        # A submillimetre inset separates point contacts introduced by the low-resolution luminous contour.
        shape=shape.buffer(-.00035,quad_segs=1,join_style='mitre').buffer(.00015,quad_segs=1,join_style='mitre')
        shape=shape.simplify(.0031 if low else .00085,preserve_topology=True)
        b.prism(shape,-.001,.038,face,SIDE,f'East {row.lower()} | letter return {i}')
        b.prism(shape,.038,.046,face,GOLD,f'East {row.lower()} | yellow face {i}')
