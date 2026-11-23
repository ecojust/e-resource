"""The separate shop inscriptions and wall lights at 143-1 in February 2018."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon

from photo_architecture import Facade
from register_street import Camera
from street_portal import FRAME, BLACK
from measure_number_plates import project_quad

DATA=json.loads((Path(__file__).parent.parent/'measurements/shop-signs.json').read_bytes())
INK='Xinlefang | white print on canvas awning'
LIT='Xinlefang | cool white lit letters'
PALETTE={INK:{'color':[.61,.60,.576],'roughness':.82},
         LIT:{'color':[.87,.91,.96],'roughness':.37,'emissive':[.42,.52,.68]}}

def add_shop_signs(builder):
    camera=Camera('2018')
    face=Facade(builder,(-1,0),(1,0),'143-1 street shop')
    for name,depth,ink in [('canopy',.315,INK),('illuminated',.109,LIT)]:
        data=DATA['signs'][name]
        corners=data['corners_full_source_px']
        if name=='illuminated':
            housing=Polygon([camera.wall(pixel,-depth)[[0,2]]for pixel in corners])
            face.prism(housing,.014,depth,BLACK,'wall-mounted sign below the street plate')
        photo=project_quad(corners)
        def ring_on_sign(ring):
            uv=np.c_[ring,np.ones(len(ring))]@photo.T
            return [camera.wall(pt[:2]/pt[2],-depth-.002)[[0,2]]for pt in uv]
        for number,rings in enumerate(data['rectified_ink_regions_uv'],1):
            shape=Polygon(ring_on_sign(rings[0]),[ring_on_sign(r)for r in rings[1:]])
            if not shape.is_valid:shape=shape.buffer(0)
            face.prism(shape,depth+.0003,depth+.002,ink,f'{name} / letter {number}')
    for name,u,v in [('left',2191,2302),('right',2749,2293)]:
        x,_,z=camera.wall((u,v),-.063)
        face.box(x,z,.069,.254,.119,.062,FRAME,f'{name} wall light')
