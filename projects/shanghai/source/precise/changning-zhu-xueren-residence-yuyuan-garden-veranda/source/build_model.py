"""Build the garden veranda and east entrance of the Zhu Xueren residence."""
import argparse
import json
import os
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
from photo_architecture import Builder as GeometryBuilder
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-gongyi-fang-975-987-sichuan-road/source'))
from asset_rights import licensed_writer,retain_metadata
sys.path.insert(0,str(SOURCE))
import east_entrance
import garden_planters
import garden_railings
import zhu_garden_doors
import zhu_garden_materials
import zhu_garden_veranda
import zhu_residence_roof
from rights import GEOMETRY_LICENSE,LICENSE_URL,PHOTO_AUTHOR,PHOTO_SOURCE,TEXTURE_LICENSE


ID='changning-zhu-xueren-residence-yuyuan-garden-veranda'
SLUG='zhu-xueren-residence-yuyuan-garden-veranda'
PALETTE={**zhu_garden_materials.PALETTE,**zhu_residence_roof.PALETTE,
         **garden_planters.PALETTE,**garden_railings.PALETTE,**east_entrance.PALETTE}
META=dict(id=ID,name='朱学仁住宅南园廊与东入口',address='上海市长宁区愚园路684号',
    viewer_page=SLUG+'.html',heritage_group='CN-J-002-V / 5M002',
    scope='2013年南园廊、五级弧形台阶、三开间楼廊、东入口雨篷和北侧弧墙，保留可辨的红瓦主坡面和三处老虎窗。',
    dimensions='主屋南檐宽18.8米。廊柱、门洞、弧阶、檐线和门廊据照片交会，屋面范围据四期影像约束。西北背面封合及部分树荫遮挡的开口简化。',
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,
    url='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
    attribution='上海市第五批优秀历史建筑5M002。南园廊依高参88的2013年摄影，东入口另参照Antigng的2018年摄影。',
    photos_embedded=False,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,
    license_url=LICENSE_URL,copyright='Original architectural geometry and procedural finishes, MIT.',
    camera_views=json.loads((SOURCE/'cameras.json').read_bytes()))


class GardenBuilder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        # Roof patches supply per-corner coordinates measured along the fall of
        # each slope. The terrazzo needs a wrap around every curved step riser.
        if material==zhu_residence_roof.TILE:
            GeometryBuilder.add(self,vertices,faces,material,label)
        else:
            super().add(vertices,faces,material,label)
            if material==zhu_garden_materials.STAIR:
                part=self.parts[-1]
                part['texcoords']=[(s*4/.78,t*4/.78) for s,t in part['texcoords']]


def add_building(builder,lod=False):
    layout=json.loads((SOURCE/'garden-layout.json').read_bytes())
    zhu_garden_veranda.add_garden(builder,lod,layout)
    zhu_garden_doors.add_gallery_back(builder,layout)
    zhu_garden_doors.add_approach_and_envelope(builder,layout,lod)
    garden_planters.add_planters(builder,lod,layout)
    garden_railings.add_railings(builder,lod,layout)
    east_entrance.add_east(builder,lod,layout)
    zhu_garden_doors.add_eastern_section(builder,layout)
    zhu_residence_roof.add_roof(builder,lod,layout)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Write one uncompressed GLB')
    parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output is not None:
        if rest:parser.error('Unexpected arguments '+str(rest))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        builder=GardenBuilder(PALETTE)
        add_building(builder,args.lod)
        report=builder.save(args.output,META)
        print(report['triangles'],report['parts'],report['bytes'],report['sha256'])
        return
    if args.lod:parser.error('--lod requires --output')
    os.environ['ZHU_RESIDENCE_BLENDER']=args.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=GardenBuilder
    pack.retain_metadata=retain_metadata
    pack.write_json=licensed_writer(pack.write_json,META)
    pack.build(SOURCE,META,PALETTE,add_building)


if __name__=='__main__':
    main()
