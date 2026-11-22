"""Rebuild Gongyi Fang building 3, 975–987 North Sichuan Road, in local metres."""
import argparse
import json
import os
import sys
from pathlib import Path

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
sys.path.insert(0,str(SOURCE))
import gongyi_balconies
import gongyi_body
import gongyi_front
import gongyi_materials
import gongyi_roof

ID='hongkou-gongyi-fang-975-987-sichuan-road'
SLUG='gongyi-fang-975-987-sichuan-road'
PALETTE={**gongyi_materials.PALETTE,**gongyi_roof.PALETTE,**gongyi_balconies.PALETTE}
META=dict(id=ID,name='公益坊四川北路975–987号商住楼（今潮8弄3号楼）',viewer_page=SLUG+'.html',
    heritage_group='HK-J-038-V / 5F038',address='上海市虹口区四川北路975–987号（单号）',
    scope='四川北路九开间修缮后街面、两层通长阳台、门窗与底铺，结合两期正射的现状屋面及简化后墙。2号楼和北侧1297–1311号另行识别。',
    dimensions='建筑约46米长。街面细部来自现场照片和总图比例，屋面设施的用途、绝对高度及隐蔽院面留有不确定性。',
    photo_author='Antigng，2018；上海章明建筑设计事务所；天华建筑设计；Esri及其影像提供者',
    photo_source='https://m.thepaper.cn/baijiahao_31065777',url='https://www.thape.com/news/833',
    attribution='虹口区政府标为3号楼。街面参考2018年及修缮后照片，屋面区分2018和修缮后形态。',
    photos_embedded=False,geometry_license='MIT for original authored architectural detail; underlying city data retains its own attribution',
    texture_license='MIT, original procedural brick and historic roof texture',license_url='https://opensource.org/license/mit',
    copyright='Original architectural modelling and procedural finishes under MIT. Documentary photographs and aerial imagery are cited and not embedded.')


def add_building(b,lod=False,roof_period=None):
    layout=json.loads((SOURCE/'front-layout.json').read_bytes())
    gongyi_body.add_body(b,layout)
    gongyi_front.add_front(b,lod,layout)
    gongyi_balconies.add_balconies(b,lod,layout)
    period=roof_period or layout['roof_period']
    if period=='after_repair':
        gongyi_roof.contemporary(b,lod,layout)
    elif period=='2018_roof_study':
        gongyi_roof.december_2018(b,lod,layout)
    else:
        raise ValueError('Unknown roof study '+period)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Write one uncompressed GLB')
    parser.add_argument('--lod',action='store_true')
    parser.add_argument('--roof-period',choices=['after_repair','2018_roof_study'],default='after_repair')
    parser.add_argument('--blender',default='blender',help='Blender executable for the complete four-file package')
    args,remaining=parser.parse_known_args()
    if args.output is None:
        if args.lod or args.roof_period!='after_repair':
            parser.error('The LOD and historical roof study options require --output')
        from asset_rights import licensed_writer,retain_metadata
        os.environ['GONGYI_3_BLENDER']=args.blender
        sys.argv[1:]=[*remaining,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=CrownBuilder
        pack.retain_metadata=retain_metadata
        pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
        return
    if remaining:
        parser.error('Unexpected arguments '+str(remaining))
    builder=CrownBuilder(PALETTE)
    add_building(builder,args.lod,args.roof_period)
    metadata=dict(META)
    if args.roof_period=='2018_roof_study':
        metadata.update(id=ID+'-2018-roof-study',name='公益坊3号楼2018年12月屋面形态研究',
                        scope='研究切换2018年可辨的沿街瓦坡和三个院侧回脊，街面仍用于对照修缮后的形态。')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    print(builder.save(args.output,metadata)['triangles'])


if __name__=='__main__':
    main()
