"""Model the courtyard section of the former Sainte-Marie maternity pavilion."""
from pathlib import Path
import argparse
import os
import sys
from shapely.geometry import box,Polygon
from shapely.ops import unary_union

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
sys.path.insert(0,str(SOURCE.parents[1]/'huangpu-somekh-building-street-corner'/'source'))
import package_architectural_model as packaging
from aggregate_mesh import AggregateBuilder
from photo_architecture import Facade
from pavilion_materials import PALETTE,BRICK,CREAM,EDGE,CUT,WOOD,DARK,BLACK,FLOOR,PLINTH,add_brick_uvs
from pavilion_windows import upper_entry,triple,timber_basement,framed
from pediments import frieze,building_number,central_gable,shaped_gable
from pavilion_roof import roof,HALF,RIDGE,HEIGHT,roof_height
from courtyard_stairs import add_stairs,STAIR_PALETTE,DECK,DECK_UNDERSIDE

ID='huangpu-guangci-maternity-pavilion-twin-stair'
TITLE='广慈医院原产科楼庭院立面与双梯门廊'
META=dict(id=ID,name=TITLE,viewer_page='guangci-maternity-pavilion-twin-stair.html',heritage_group='4C018',
    status='courtyard-elevation-from-historic-and-modern-photographs',heritage_address='瑞金二路197号',
    scope='原广慈医院25舍、今8号楼。制作庭院中央门廊、左右双梯和平台，中央题名山花、两侧最近的曲线山花，以及七个窗轴所对应的屋面段。截面以外的长翼、室内和院区其他建筑仍在调查。',
    estimated='两张2018年庭院照片以共同构件配准。以一皮砖含灰缝约65毫米作比例假设。模型尺寸为照片估计，各级阶梯的踏深和上段级数、屋面截深也包含估值。',
    reference_height_m=16.73,construction_date_sources={'2005年市政府遗产铭牌':1921,'2020年瑞金医院院史':1922},original_use='产科病房',current_building_number=8,
    coordinate_convention='Local metres, Z up from courtyard, X to the right as seen from the courtyard, +Y into the building from the upper central facade. No surveyed world position is implied.',
    source_register='source/precise/'+ID+'/reference-review.json',photos_embedded=False,interiors_modeled=False,third_party_models_embedded=False)
PALETTE.update(STAIR_PALETTE)
packaging.Builder=AggregateBuilder


def porch_light(face,x,z,lod):
    face.box(x,z,.19,.42,.20,.13,BLACK,'wall lantern mounting plate')
    face.box(x,z+.06,.18,.25,.18,.29,CREAM,'lantern frosted glass')
    for dx in [-.085,.085]:
        face.box(x+dx,z+.06,.021,.28,.018,.392,BLACK,'lantern uprights')
    face.prism(Polygon([(x-.15,z+.19),(x+.15,z+.19),(x,z+.34)]),.19,.39,BLACK,'lantern cap')
    face.box(x,z-.14,.13,.045,.19,.29,BLACK,'lantern base')


def wing_section(b,face,x0,x1,centres,lod,central=False):
    floor=4.08 if central else 4.14
    head=9.30 if central else 9.20
    holes=[]
    for i,x in enumerate(centres):
        holes.append(triple(face,x,floor,head,3.68,lod,'upper bay '+str(i+1)))
        if not central:
            holes.append(triple(face,x,.52,3.68,3.60,lod,'lower bay '+str(i+1)))
    if central:
        holes.append(upper_entry(face,lod,DECK+.018))
        for x in [-1.95,1.95]:porch_light(face,x,7.70,lod)
    face.prism(box(x0,0,x1,11.28).difference(unary_union(holes)),-.27,0,BRICK,'brick wall cut through at each opening')
    wallbase=box(x0,0,x1,.49).difference(unary_union(holes))
    face.prism(wallbase,-.015,.055,PLINTH,'courtyard stone skirting')
    frieze(face,x0,x1,9.42 if central else 9.32,lod)


def courtyard_basement(b,lod):
    extent=6.80;y=-3.12
    face=Facade(b,(-extent,y),(extent,y),'terrace basement')
    holes=[timber_basement(face,lod)]
    for x in [-5.05,5.05]:
        p=box(x-1.04,.57,x+1.04,3.36);holes.append(p)
        framed(face,p,'courtyard windows',lod,3,[(1.08,.09),(2.75,.085)])
    face.prism(box(-extent,0,extent,DECK_UNDERSIDE).difference(unary_union(holes)),-.20,0,BRICK,'red brick under terrace')
    face.prism(box(-extent,.02,extent,.62).difference(unary_union(holes)),-.015,.07,PLINTH,'terrace basement base')
    for x in [-2.30,2.30]:
        face.box(x,1.79,.37,3.50,.20,.044,BRICK,'brick reveals under central stone piers')
    for x in [-extent,extent]:
        b.box((x,-1.59,DECK_UNDERSIDE/2),(.18,3.01,DECK_UNDERSIDE),BRICK,label='basement side returns to upper wall')


def add_building(b,lod):
    mid=Facade(b,(-HALF,0),(HALF,0),'courtyard centre')
    wing_section(b,mid,-8.13,8.13,(-5.18,5.18),lod,central=True)
    for side in [-1,1]:
        wings=Facade(b,(-HALF,.48),(HALF,.48),'right wing' if side>0 else 'left wing')
        x0,x1=sorted([side*8.13,side*HALF])
        wing_section(b,wings,x0,x1,(side*10.56,side*16.12),lod)
        b.box((side*8.13,.24,5.61),(.15,.49,11.22),BRICK,label='side reveal at central frontage projection')
    for x in [-19.6,-13.37,-7.86,-2.48,2.48,7.86,13.37,19.6]:
        face=mid if abs(x)<8.14 else Facade(b,(-HALF,.48),(HALF,.48),'right wing' if x>0 else 'left wing')
        face.box(x,6.05,.32,6.58,.12,.032,BRICK,'brick pier forming upright between window axes')
    building_number(mid);central_gable(mid,lod)
    for x in [-16.14,16.14]:
        wing=Facade(b,(-HALF,.48),(HALF,.48),'right attic' if x>0 else 'left attic')
        shaped_gable(wing,x,lod)
    courtyard_basement(b,lod)
    add_stairs(b,lod)
    roof(b,lod)
    # Only the documented courtyard section is modelled. The tall neutral
    # cut faces are inside the outermost piers, not invented end elevations.
    section=Polygon([(.49,.02),(RIDGE,.02),(RIDGE,HEIGHT),(.49,roof_height(.49))])
    for near,far in [(-HALF,-HALF+.085),(HALF-.085,HALF)]:
        b.prism(section,near,far,lambda y,z,x:(x,y,z),CUT,'cut edge at adjoining wing')
    b.box((0,RIDGE-.07,HEIGHT/2),(HALF*2,.14,HEIGHT),CUT,label='section plane beneath ridge')
    b.box((0,2.97,-.008),(HALF*2,5.77,.040),FLOOR,label='model section base')
    add_brick_uvs(b)


if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    selected,rest=options.parse_known_args()
    os.environ['GUANGCI_PAVILION_BLENDER']=selected.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'native_blender.py')]
    packaging.build(SOURCE,META,PALETTE,add_building)
