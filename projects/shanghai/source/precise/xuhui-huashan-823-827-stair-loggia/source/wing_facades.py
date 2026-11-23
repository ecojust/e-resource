"""West-facing pair of gables and the narrower connecting bays, 823–827 Huashan Road.

The sash and ventilation block openings pass through the roughcast face. The
central stair loggia has its own author and meets the two inner wall ends.
"""
import json
from math import ceil
from pathlib import Path

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from placement import Facade
from wing_finishes import ROUGHCAST, PALETTE as RENDER
from wing_openings import (DARK, ROD, CLAY, PALETTE as FITTINGS, opening, sash,
                           awning, vent_outline, geometric_vent)

HERE = Path(__file__).resolve().parent
LAYOUT = json.loads((HERE/'wing_layout.json').read_text())['wings']
PALETTE = {**FITTINGS, **RENDER}
WALL_DEPTH = .28


def _verge(face, x0, z0, x1, z1, lod):
    """Small overlapping caps visible on the outer gable edges."""
    fall = (z1-z0)/(x1-x0)
    count = max(1,ceil((x1-x0)/(.72 if lod else .39)))
    for i in range(count):
        a=x0+(x1-x0)*i/count
        b=x0+(x1-x0)*(i+1)/count
        overlap = .021 if i+1<count else 0.
        p,q=(a,-.023,z0+fall*(a-x0)+.001),(b+overlap,-.023,z0+fall*(b+overlap-x0)+.001)
        face.rail([p,q],.058,CLAY,'individual red clay verge cap',8 if lod else 12)


def add_wings(b,lod=False):
    for name, panel in LAYOUT.items():
        face=Facade(b,origin=(0.,panel.get('y',0.)),label='Huashan west elevation | '+name)
        x0,x1=panel['x0'],panel['x1']
        za,zb=panel['outer_eave'],panel['inner_eave']
        chain=[(x0,za)]
        if 'ridge' in panel:
            chain.append(tuple(panel['ridge']))
        chain.append((x1,zb))
        polygon=Polygon([(x0,0.),(x1,0.),*reversed(chain)])
        windows=panel.get('windows',{})
        vents=panel.get('vents',{})
        holes=[opening(v['bounds'],v['fan'],lod) for v in windows.values()]
        holes.extend(vent_outline(v['bounds'],v['cells']) for v in vents.values())
        slots=[box(*bb) for bb in panel.get('slot_bounds',[])]
        face.solid(polygon.difference(unary_union(holes+slots)),-WALL_DEPTH,0.,ROUGHCAST,
                   'roughcast exterior and opening reveals')
        for key,v in windows.items():
            kw=dict(arched=v['fan'],columns=v['columns'],rows=v['rows'],lod=lod)
            sash(face,v['bounds'],key,**kw)
            if v['hood']:
                awning(face,v['bounds'],key+' | folding awning',retract=v['fan'],lod=lod,
                       measurements=v.get('awning_measurements'))
        for key,v in vents.items():
            geometric_vent(face,v['bounds'],key,v['cells'],lod)
        for slot in slots:
            # The upper lip is visible through each narrow hole. Its inside face is dark.
            lining=slot.difference(slot.buffer(-.003,join_style=2))
            face.solid(lining,-WALL_DEPTH,-.017,DARK,'dark inner return of rectangular air slot')
            face.solid(slot,-WALL_DEPTH-.012,-WALL_DEPTH,DARK,'slot recess')
        if 'ridge' in panel:
            for left,right in zip(chain,chain[1:]):
                _verge(face,*left,*right,lod)
        else:
            # The short side bay has a continuous dark horizontal drip, not clay verge caps.
            face.band(chain,.089,-.026,.069,ROD,'dark drip over connecting bay')
