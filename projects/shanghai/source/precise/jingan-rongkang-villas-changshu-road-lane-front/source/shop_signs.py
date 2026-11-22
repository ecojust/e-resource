"""Raised 2017 lettering on the four shop fascias beside the south Rongkang Villas entrance."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon

MEASUREMENTS = Path(__file__).resolve().parents[1]/'measurements'
INSCRIPTIONS = json.loads((MEASUREMENTS/'2017-shop-sign-inscriptions.json').read_bytes())['panels']
FINISH = {
    'pink': ('Salon | raspberry lettering', [223,74,171], .024),
    'white': ('Clothing | white lettering', [235,235,237], .033),
    'wine': ('East fascia | dark red lettering', [83,26,36], .018),
    'pale': ('Fangyou | pale lettering', [194,191,187], .019),
    'blue': ('Fangyou | blue roof chevron', [34,88,134], .018)}
SIDES = {
    'pink': ('Salon | grey mauve return', [122,96,112]),
    'white': ('Clothing | dark blue return', [53,53,89]),
    'wine': ('East fascia | pale metal return', [162,153,143]),
    'pale': ('Fangyou | muted edge', [126,124,121]),
    'blue': ('Fangyou | blue edge', [42,74,100])}


def finish(rgb):
    srgb=np.asarray(rgb,dtype=float)/255
    return {'color':np.where(srgb>.04045,((srgb+.055)/1.055)**2.4,srgb/12.92).tolist(),'roughness':.65}


PALETTE = {v[0]:finish(v[1]) for v in [*FINISH.values(),*SIDES.values()]}


def panel_mapper(corners):
    """Interpolate photo-left bottom, right bottom, right top and left top; d is metres outward."""
    bl,br,tr,tl=np.asarray(corners,dtype=float)
    outward=np.cross((br-bl)+(tr-tl),(tl-bl)+(tr-br))
    length=np.linalg.norm(outward)
    if length<1e-9:raise ValueError('Degenerate shop sign panel')
    outward=outward/length
    def point(u,v,d):
        left=bl+v*(tl-bl); right=br+v*(tr-br)
        return left+(u+.5)*(right-left)+outward*d
    return point


def add_shop_signs(builder,lod=False,panels=None):
    """Add four separate inscriptions. Each backing board belongs to the facade model."""
    if panels is None:
        panels=json.loads((MEASUREMENTS/'shop-panel-geometry.json').read_bytes())['world_panels']
    level='low' if lod is True or lod=='lod' else 'near'
    for board,letters in INSCRIPTIONS.items():
        point=panel_mapper(panels[board])
        for number,letter in enumerate(letters,1):
            key=letter['surface']
            face,_,depth=FINISH[key]
            description=board.replace('north_','N ')+f' {number:02d}'
            for i,rings in enumerate(letter[level],1):
                polygon=Polygon(rings[0],rings[1:])
                if not polygon.is_valid or polygon.area<=0:
                    raise ValueError((board,letter['lettering'],i))
                name=f'{description} piece {i:02d}'
                if level=='near':
                    builder.prism(polygon,-.001,depth-.003,point,SIDES[key][0],name+' | return')
                    builder.prism(polygon,depth-.003,depth,point,face,name+' | face')
                else:
                    builder.prism(polygon,-.001,depth,point,face,name)


PIER_BLUE = 'Fangyou | blue pier inscription'
PIER_EDGE = 'Fangyou | painted blue edge'
PALETTE[PIER_BLUE] = finish([32,46,106])
PALETTE[PIER_EDGE] = finish([39,51,89])


def add_south_pier_words(builder,lod=False,panels=None):
    """Two separately measured four-character columns on the shop entrance in 2017."""
    if panels is None:
        panels=json.loads((MEASUREMENTS/'south-shop-pier-panels.json').read_bytes())['world_panels']
    words=json.loads((MEASUREMENTS/'2017-south-pier-words.json').read_bytes())['panels']
    level='low' if lod is True or lod=='lod' else 'near'
    for column,letters in words.items():
        point=panel_mapper(panels[column])
        for n,letter in enumerate(letters,1):
            for i,rings in enumerate(letter[level],1):
                poly=Polygon(rings[0],rings[1:])
                if not poly.is_valid or poly.area<=0:
                    raise ValueError((column,n,i))
                name=f'Blue shop column {column[5:]} {n} {i}'
                if level=='near':
                    builder.prism(poly,-.001,.0045,point,PIER_EDGE,name+' edge')
                    builder.prism(poly,.0045,.006,point,PIER_BLUE,name+' face')
                else:
                    builder.prism(poly,-.001,.006,point,PIER_BLUE,name)
