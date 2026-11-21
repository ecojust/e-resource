"""The photographed seven-axis, north-facing street wall of 1295 South Suzhou Road."""
import argparse
import json
import os
import sys
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
sys.path.insert(0,str(SOURCE.parents[1]/'hongkou-general-post-office/source/common'))
from photo_architecture import Facade
from package_architectural_model import build
import arch_windows
import warehouse_brick
import warehouse_entry
import warehouse_front as front

ID = 'huangpu-fifth-textile-warehouse-river-front'
D = json.loads((SOURCE/'dimensions.json').read_bytes())
SCOPE = '南苏州路1295号临河街面，以2019年和2020年实拍为准，含两排共十四樘弧券窗、中央方门、左右店面、山花及紧接山墙的屋面首段。'
META = dict(id=ID,name='中国纺织建设公司第五仓库临河弧券窗与中央门洞',
            model_scope_zh=SCOPE,scope=SCOPE,viewer_page='fifth-textile-warehouse-river-front.html',
            status='restored-north-warehouse-front',
            third_party_materials=[dict(material=warehouse_brick.MATERIAL,author='Livelikerw',title='1295 South Suzhou Rd. Shanghai.JPG',license='CC BY-SA 4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/',source_url='https://commons.wikimedia.org/wiki/File:1295_South_Suzhou_Rd._Shanghai.JPG',changes='Rectified masonry sample, mirrored and blended with procedural mortar and lime.',credit='source/precise/'+ID+'/source/brick-credit.md')],
            source_register=f'source/precise/{ID}/reference-review.json',
            reference_height_m=round(D['height_m'],4),
            coordinate_convention='Metres. Positive X runs west across the north face, negative Y is the street, and Z is up. The origin is between the central pilasters at pavement level.',
            interiors_modeled='临街门槛、玻璃砖门套与可见入口首段。仓库纵深、内部办公层和后院另列调查。')
IRON='Dull corrugated metal roof'
GUTTER='Oxidised rainwater metal'
PALETTE={**front.PALETTE,**arch_windows.PALETTE,**warehouse_entry.PALETTE,
         IRON:front.finish((134,136,128),.82,.21),GUTTER:front.finish((100,104,96),.74,.25)}


def street_roof(builder, facade, d, lod):
    half=d['wall_width']/2
    depth=d['roof_first_span']
    crown=d['height_m']-.78
    edge=11.08
    # Roof ridge behind the triangular gable, recorded in the pre-conversion
    # aerial photograph. Only the front span of the long roof is included.
    def surface(x):
        return crown-(crown-edge)*abs(x)/half
    ends=[-half+.09,0,half-.09]
    for a,b in zip(ends,ends[1:]):
        xz=Polygon([(a,surface(a)-.14),(b,surface(b)-.14),(b,surface(b)),(a,surface(a))])
        facade.prism(xz,-depth,-.48,IRON,'Twin pitched sheets behind the river gable')
    if not lod:
        for j in range(1,6):
            y=.51+j*.68
            for a,b in zip(ends,ends[1:]):
                builder.tube([(a,y,surface(a)+.010),(b,y,surface(b)+.010)],.019,GUTTER,6,'Sheet-metal lap seams')
    builder.tube([(0,.49,crown+.012),(0,depth,crown+.012)],.085,IRON,8 if lod else 12,'Folded ridge cap')
    for side in (-1,1):
        x=side*(half-.30)
        # The two side returns continue to the eaves. The street-front survey
        # does not establish opening positions across the rest of either wall.
        width=.42
        if side<0:
            sections=[(0,edge-.09,depth)]
        else:
            neighbour=d['west_adjacent_roof_m']+.07
            sections=[(0,neighbour,d['west_low_return_m']),(neighbour,edge-.09,depth)]
        for low,high,limit in sections:
            section=Polygon([(x-width/2,low),(x+width/2,low),(x+width/2,high),(x-width/2,high)])
            facade.prism(section,-limit,-.45,warehouse_brick.MATERIAL,'Short brick return behind the gable')
        builder.tube([(side*(half-.02),.44,edge-.095),(side*(half-.02),depth,edge-.095)],
                     .073,GUTTER,7 if lod else 11,'Gutter on flank of warehouse')
        front_x=side*(half-.47)
        facade.line((front_x,11.66,.13),(front_x,.30,.13),.065,GUTTER,7 if lod else 11,'Downpipe at outer pier')
        if not lod:
            for z in (1.,4.15,7.87,11.35):
                facade.box(front_x,z,.18,.048,.20,.086,front.SLATE,'Drainpipe collar')


def add_geometry(builder, lod):
    d=D
    half=d['wall_width']/2
    facade=Facade(builder,(-half,0),(half,0),'Fifth Warehouse north elevation')
    outer=front.poly_from_profile(d)
    street_openings=front.shop_openings(d)
    left,sill,right,head=street_openings['portal'].bounds
    # Put the masonry substrate beneath the finished threshold. The visible tread
    # continues into the vestibule through the full thickness of the old wall.
    street_openings['portal']=box(left-.006,sill-.006,right+.006,head+.006)
    cuts=[*arch_windows.apertures(d,lod),*street_openings.values(),*front.upper_vents(d)]
    wall=outer.difference(unary_union(cuts))
    assert wall.is_valid and all(cut.within(outer.buffer(.02)) for cut in cuts)
    facade.prism(wall,-.55,0,warehouse_brick.MATERIAL,'Original clear-brick wall with open arches')
    front.bay_masonry(facade,d,lod)
    front.belts(facade,d,lod)
    arch_windows.install(facade,d,lod)
    front.shops(facade,d,lod)
    front.front_display(facade,d,lod)
    roof_sign=front.upper_front(facade,d,lod)
    warehouse_entry.install(facade,d,lod)
    warehouse_entry.roof_letters(facade,d,lod,*roof_sign)
    street_roof(builder,facade,d,lod)
    warehouse_brick.apply(builder)


if __name__=='__main__':
    sub=argparse.ArgumentParser(add_help=False)
    sub.add_argument('--blender',default='blender')
    args,rest=sub.parse_known_args()
    os.environ['FIFTH_WAREHOUSE_BLENDER']=args.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_geometry)
