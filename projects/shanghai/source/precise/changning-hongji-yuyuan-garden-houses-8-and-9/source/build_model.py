"""Reconstruct garden houses 8 and 9 at 1107 Yuyuan Road, each in its own surveyed frame."""
import argparse
import json
import os
from pathlib import Path
import sys

import garden_builder
from garden_builder import GardenBuilder, PROJECT, SOURCE
from garden_fabric import PALETTE as FINISHES, GLASS, LEDGE, METAL, WOOD, face
from garden_shells import add_shell, porch_sash
import courtyard
import eight_cafe_signs
import eight_gable
import hongji_roof_geometry
import house_eight_entrances
import house_nine_sashes
import nine_portico
import nine_side_facades
import rainwater
import roof_8
import roof_9
from hongji_rights import GEOMETRY_LICENSE, LICENSE_URL, PHOTO_AUTHOR, PHOTO_SOURCE, TEXTURE_LICENSE
from shapely.geometry import box

sys.path.insert(0,str(PROJECT/'source/precise/hongkou-gongyi-fang-975-987-sichuan-road/source'))
from asset_rights import licensed_writer, retain_metadata

ID='changning-hongji-yuyuan-garden-houses-8-and-9'
SLUG='hongji-yuyuan-garden-houses-8-and-9'
PALETTE={**FINISHES,**eight_gable.PALETTE,**house_eight_entrances.PALETTE,**eight_cafe_signs.PALETTE,
         **hongji_roof_geometry.PALETTE,**house_nine_sashes.PALETTE,**rainwater.PALETTE}
META=dict(id=ID,name='弘基创意国际园——8、9号楼',address='上海市长宁区愚园路1107号',
          viewer_page=SLUG+'.html',heritage_group='5M010',period='2023',
          scope='草坪两边分立的8号、9号花园住宅，含前后错开的屋脊、门廊和两宅之间的庭院。',
          dimensions='两处朝向庭园的主山墙墙脚宽约7.12米和7.27米，正面中点相距约26.28米。尺寸由地面照片和航片估算。',
          photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,photos_embedded=False,
          url='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
          attribution='上海市第五批优秀历史建筑5M010登记为上海长征制药厂。8号和9号分别凭门牌、庭院对景和实拍山墙辨认。建模采用2023年9月发布照片所示外观，2015、2016年旧照补充量测。',
          geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,license_url=LICENSE_URL,
          copyright='Original reconstructed geometry and four procedural architectural finishes: MIT. Source photographs are credited and are not embedded.',
          camera_views=json.loads((SOURCE/'cameras.json').read_bytes()))


def balcony_window(b):
    plane=nine_portico.dimensions()['door_plane_y']
    outer=porch_sash();inner=outer.buffer(-.070,join_style=2)
    face(b,outer.difference(inner),plane+.03,plane+.16,WOOD,'9 | upper porch opening surround')
    l,lo,r,hi=inner.bounds
    face(b,box(l-.10,hi+.07,r+.10,hi+.165),plane-.085,plane+.045,LEDGE,'9 | upper porch window head')
    for j in range(3):
        a=l+(r-l)*j/3;c=l+(r-l)*(j+1)/3
        if j:face(b,box(a-.028,lo,a+.028,hi),plane+.062,plane+.14,METAL,'9 | upper porch window mullion')
        face(b,box(a+(.028 if j else 0),lo,c-(.028 if j<2 else 0),hi),plane+.154,plane+.173,
             GLASS,'9 | upper porch window glass')


def add_house(local,number,layout,lod=False):
    """Author one house in local axes, including its photographed plantings."""
    if number==8:
        add_shell(local,number,layout)
        eight_gable.add_gable(local,lod,layout)
        house_eight_entrances.add_entrances(local,lod,layout)
        eight_cafe_signs.add_signs(local,lod,layout)
        roof_8.add_roof(local,lod,layout)
    else:
        import nine_north_windows
        add_shell(local,number,layout,nine_north_windows.openings(layout))
        house_nine_sashes.add_sashes(local,lod,layout)
        nine_portico.add_portico(local,lod,layout)
        nine_portico.porch_lighting(local,lod)
        balcony_window(local)
        nine_side_facades.add_facades(local,lod,layout)
        nine_north_windows.add_windows(local,lod,layout)
        roof_9.add_roof(local,lod,layout)
    rainwater.add_downpipes(local,number,lod,layout)
    courtyard.planted_edges(local,number,lod)


def add_building(b,lod=False):
    layouts=json.loads((SOURCE/'garden-layout.json').read_bytes())
    for number in (8,9):
        layout=layouts[str(number)];local=GardenBuilder(PALETTE)
        add_house(local,number,layout,lod)
        b.place_house(local,number,layout['garden_transform'])
    courtyard.add_garden(b,layouts)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown arguments '+str(rest))
        b=GardenBuilder(PALETTE);add_building(b,args.lod)
        result=b.save(args.output,META)
        print(result['triangles'],result['parts'],result['bytes'],result['sha256'])
        return
    if args.lod:parser.error('--lod requires --output')
    os.environ['HONGJI_GARDEN_BLENDER']=args.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
    pack=garden_builder.packaging
    pack.Builder=GardenBuilder
    pack.retain_metadata=retain_metadata
    pack.write_json=licensed_writer(pack.write_json,META)
    pack.build(SOURCE,META,PALETTE,add_building)


if __name__=='__main__':
    main()
