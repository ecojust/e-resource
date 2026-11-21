"""Reconstruct the exterior of the garden villa at 517 Fuxing Middle Road."""
import argparse
import os
import sys
from pathlib import Path

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
sys.path.insert(0,str(SOURCE.parents[1]/'huangpu-somekh-building-street-corner'/'source'))
sys.path.insert(0,str(SOURCE))
import package_architectural_model as packaging
from aggregate_mesh import AggregateBuilder
from villa_materials import PALETTE,add_uvs
from villa_roof import add_roof,ROOF_PALETTE
from villa_walls import wall_shell,garden_gallery,west_study
from garden_details import terrace_and_porch,street_ivy
from east_portal import cut_shape,east_entrance

ID='huangpu-liu-yazi-residence-fuxing-517'
TITLE='柳亚子旧居（思南书局）主楼与东侧砖券入口'
META=dict(id=ID,name=TITLE,viewer_page='liu-yazi-residence-fuxing-517.html',
    status='restored-villa-exterior-from-floor-plans-sections-and-photographs',
    reference_height_m=16.65,
    scope='复兴中路517号花园住宅主楼外壳、东侧弧形阶梯和红色券廊、南庭院双层玻璃廊、露台、南北山墙与交叉坡屋顶。沿街相邻住宅和外围庭院不计入。',
    estimated='主楼尺度由修缮方四层平面和两张剖面配准获得。门券和低檐以两次街景独立复核。五金、砖缝、材色、屋瓦及绿化细部依据2018年修缮后影像估计。',
    coordinate_convention='Metres, Z up above the south garden grade. Origin is the centre of the rectangular block. Local X follows the garden facade at azimuth 78.3677 degrees; +Y points north-northwest to Fuxing Middle Road.',
    heritage_group='4C014',heritage_address='上海市黄浦区复兴中路517号',interiors_modeled=False,
    source_register='source/precise/'+ID+'/reference-review.json',photos_embedded=False,third_party_models_embedded=False)
PALETTE.update(ROOF_PALETTE)
packaging.Builder=AggregateBuilder


def add_building(builder,lod):
    _,east,north=wall_shell(builder,lod,cut_shape(lod))
    garden_gallery(builder,lod)
    west_study(builder,lod)
    east_entrance(east,lod)
    terrace_and_porch(builder,lod)
    street_ivy(north,lod)
    add_roof(builder,lod,{})
    add_uvs(builder)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    opts,rest=parser.parse_known_args()
    os.environ['SINAN_BOOKS_BLENDER']=opts.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    packaging.build(SOURCE,META,PALETTE,add_building)
