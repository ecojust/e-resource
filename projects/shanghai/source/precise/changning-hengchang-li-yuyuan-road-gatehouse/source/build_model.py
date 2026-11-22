"""Build the southern gatehouse and first attached street range at Hengchang Li."""
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
from asset_rights import licensed_writer, retain_metadata
sys.path.insert(0,str(SOURCE))
import awning
import east_balconies
import entrance_relief
import exterior_sashes
import gate_passage
import passage_entrance_soffit
import gatehouse_finishes
import hengchang_roof
import street_envelope
import street_shops
import west_blind_arch
from rights import GEOMETRY_LICENSE, LICENSE_URL, PHOTO_AUTHOR, PHOTO_SOURCE, TEXTURE_LICENSE

ID='changning-hengchang-li-yuyuan-road-gatehouse'
SLUG='hengchang-li-yuyuan-road-gatehouse'
PALETTE={**gatehouse_finishes.PALETTE,**exterior_sashes.PALETTE,**gate_passage.PALETTE,
         **entrance_relief.PALETTE,**hengchang_roof.PALETTE,**east_balconies.PALETTE,**street_shops.PALETTE,
         **west_blind_arch.PALETTE,**passage_entrance_soffit.PALETTE}
META=dict(id=ID,name='亨昌里愚园路南口过街楼与东侧街屋',address='上海市长宁区愚园路1376弄南口',
          viewer_page=SLUG+'.html',heritage_group='5M006',period='2022',
          scope='更新后的南过街楼、东侧第一段相接的街屋、南北通廊及其展陈。另有2018年旧貌独立模型。',
          dimensions='街口宽约6.34米、通口宽约4.45米，东段自门楼起约29.5米，通廊深约16.2米。尺寸由影像估计。',
          photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,photos_embedded=False,
          url='https://www.shcn.gov.cn/col314/20250805/1295665.html',
          attribution='第五批优秀历史建筑5M006。通过Antigng的2018年街面照、2015–2021年分期街景、2022年和2025年长宁官方改造实照比对。',
          geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,license_url=LICENSE_URL,
          copyright='Original architectural geometry and procedural finishes, MIT; Noto Serif glyph outlines, SIL OFL 1.1.',
          camera_views=json.loads((SOURCE/'cameras.json').read_bytes()))


class GatehouseBuilder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        if material==hengchang_roof.TILE:
            GeometryBuilder.add(self,vertices,faces,material,label)
        else:
            super().add(vertices,faces,material,label)


def metadata(period):
    if period=='2018':
        return {**META,'name':'亨昌里南口过街楼，2018年街面旧貌','period':'2018',
                'scope':'2018年2月10日街口旧貌，包括黄色墙面、石拱窗、青绿色小雨篷与当年的沿街店面。旧通廊采用当时可核的素墙。'}
    return dict(META)


def add_building(b,lod=False,period='2022'):
    layout=json.loads((SOURCE/'gatehouse-layout.json').read_bytes())
    layout['period']=period
    shops=street_shops.storefront_openings(layout)
    street_envelope.add_envelope(b,lod,layout,shops)
    west_blind_arch.add_west_arch(b,lod,layout)
    exterior_sashes.add_sashes(b,lod,layout)
    street_shops.add_storefront(b,lod,layout)
    east_balconies.add_balconies(b,lod,layout)
    hengchang_roof.add_roof(b,lod,layout)
    gate_passage.add_passage(b,lod,layout)
    if period=='2022':
        passage_entrance_soffit.add_soffit(b,lod,layout)
        awning.add_awning(b,lod,layout)
        entrance_relief.add_relief(b,lod,layout)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--period',choices=['2018','2022'],default='2022')
    parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    info=metadata(args.period)
    if args.output:
        if rest:parser.error('Unexpected arguments '+str(rest))
        b=GatehouseBuilder(PALETTE)
        add_building(b,args.lod,args.period)
        report=b.save(args.output,info)
        print(report['triangles'],report['parts'],report['bytes'],report['sha256'])
        return
    if args.lod:parser.error('--lod requires --output')
    os.environ['HENGCHANG_LI_BLENDER']=args.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=GatehouseBuilder
    pack.retain_metadata=retain_metadata
    pack.write_json=licensed_writer(pack.write_json,info)
    pack.build(SOURCE,info,PALETTE,lambda b,lod:add_building(b,lod,args.period))


if __name__=='__main__':
    main()
