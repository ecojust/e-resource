"""Map the measured window elevation and build its repeating brick finishes."""
import json
from math import log
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from shapely import set_precision
from shapely.geometry import Polygon, box

SOURCE = Path(__file__).absolute().parent
PROJECT = next(p for p in (*SOURCE.parents,Path.cwd(),*Path.cwd().parents)
               if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(PROJECT/'tools'))
import package_architectural_model
sys.path.insert(0, str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder

GRAY = 'Nanlin | grey facing brick'
RED = 'Nanlin | red stringcourse brick'
RED_STONE = 'Nanlin | deep red coping brick'
MORTAR = 'Nanlin | lime joints'
STONE = 'Nanlin | warm carved stone'
FRAME = 'Nanlin | dark window sash'
GLASS = 'Nanlin | smoky glazing'
IRON = 'Nanlin | ironwork'
DARK = 'Nanlin | reveal shadow'


def paint(rgb, roughness=.84, metallic=0):
    return dict(color=[(v/255)**2.2 for v in rgb], roughness=roughness, metallic=metallic)


PALETTE = {
    GRAY: dict(color=[1,1,1], roughness=.93, texture=str(SOURCE/'grey-brick.png')),
    RED: dict(color=[1,1,1], roughness=.92, texture=str(SOURCE/'red-brick.png')),
    RED_STONE: paint((115,62,48)),
    MORTAR: paint((161,142,124)),
    STONE: paint((190,172,145)),
    FRAME: paint((65,64,58),.59,.15),
    GLASS: paint((80,99,103),.22,.27),
    IRON: paint((56,55,50),.56,.37),
    DARK: paint((46,42,39)),
}
# The four published bed-joint periods determine relative scale across the
# photo. Its 1,955-pixel front spans the longer side of the relocated building.
# The four ortho-image roof lengths set the effective brick-and-joint module.
LAYOUT = json.loads((SOURCE/'building-layout.json').read_text())
MID_COURSE_M = LAYOUT['effective_course_m']
PITCH_SLOPE, PITCH_AT_ZERO = np.polyfit(
    [352.5,756.,1463.5,1637.5], [3.682,3.658,3.350,3.262], 1)
BELT = np.polyfit([404,722,938,1128,1460,1613,1752,1915,1974],
                  [614,621,623,627,645,648,656,660,663], 2)
REFERENCE_BELT_Z = LAYOUT['window_reference_belt_height_m']
ORIGIN_U = 119.
OBLIQUE_FACTOR = 1.026


def metric(u, v):
    """Return local seam coordinates x,z for a point on the window wall."""
    belt_v = float(np.polyval(BELT,u))
    u_on_belt = u - (u-1072.)*(v-belt_v)/33000.
    pitch = PITCH_AT_ZERO + PITCH_SLOPE*u_on_belt
    x = (MID_COURSE_M*OBLIQUE_FACTOR/PITCH_SLOPE
         * log(pitch/(PITCH_AT_ZERO+PITCH_SLOPE*ORIGIN_U)))
    z = REFERENCE_BELT_Z + (float(np.polyval(BELT,u_on_belt))-v)*MID_COURSE_M/pitch
    return float(x),float(z)


def chart(points):
    return Polygon([metric(u,v) for u,v in points])


def polygons(shape):
    cleaned = set_precision(shape, .00001).simplify(.000012, preserve_topology=True)
    return [p for p in getattr(cleaned,'geoms',[cleaned]) if p.geom_type=='Polygon' and p.area>1e-7]


def face(builder, shape, front, back, material, label):
    for poly in polygons(shape):
        builder.prism(poly,-back,-front,lambda x,z,n:(x,-n,z),material,label)


class NanlinBuilder(CrownBuilder):
    def add(self, vertices, faces, material='limestone', label='detail'):
        before = len(self.parts)
        super().add(vertices,faces,material,label)
        if len(self.parts)>before and material in (GRAY,RED):
            coords = np.array(self.parts[-1]['texcoords'], dtype=float)
            coords[:,0] /= .78*(1.44*MID_COURSE_M/.063)
            coords[:,1] /= .78*(MID_COURSE_M*20)
            self.parts[-1]['texcoords'] = coords.tolist()


def make_bricks(path, red):
    # Four pairs of a header and a stretcher repeat across each row. Bed
    # joints run through the corners of the tile and the UV scale is metric.
    rng = np.random.default_rng(5001 if red else 5002)
    height,width=500,576
    yy,xx=np.mgrid[:height,:width]
    row=yy//25
    u=(xx+np.where(row%2==0,0,72))%width
    pair=u//144
    within=u%144
    short=(row%4<=1)
    seam=np.where(short,48,96)
    brick=(within>=seam).astype(int)
    border=np.minimum.reduce([within,143-within,np.abs(within-seam)])
    vertical=yy%25
    joint=np.minimum(border,np.minimum(vertical,24-vertical)*.94)
    grain=rng.normal(0,3.8,(height,width))
    mottling=np.asarray(Image.fromarray(rng.integers(0,255,(84,96),dtype=np.uint8)).resize(
        (width,height),Image.Resampling.BICUBIC),dtype=float)/255-.5
    variation=rng.normal(0,8,(20,4,2))[row,pair,brick]
    pigment=np.array([150,77,55] if red else [81,80,79])
    lime=np.array([178,148,126] if red else [152,147,138])
    weight=np.clip((joint-(.95+.3*mottling))/1.7,0,1)[:,:,None]
    brick_rgb=pigment+(grain+variation+8*mottling+np.minimum(joint-4,0)*2.2)[:,:,None]
    mortar_rgb=lime+(grain*.62+9*mottling)[:,:,None]
    out=weight*brick_rgb+(1-weight)*mortar_rgb
    Image.fromarray(np.clip(out,0,255).astype('uint8')).save(path,optimize=True)


if __name__=='__main__':
    make_bricks(SOURCE/'grey-brick.png',False)
    make_bricks(SOURCE/'red-brick.png',True)
