"""Build the Tanggu Road Art Deco upper crown as a local architectural exhibit."""
import argparse
import json
import os
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(SOURCE))
from crown_builder import CrownBuilder
import crown_masonry
import crown_window_sashes
import dated_cartouche
from rights import GEOMETRY_LICENSE,PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,TEXTURE_LICENSE

SLUG='hongkou-tanggu-road-apartment-dated-crown'
META=dict(id=SLUG,name='公安大楼塘沽路年份匾与双塔楼冠',viewer_page='tanggu-road-apartment-dated-crown.html',
          heritage_group='5F002',scope='两侧切角楼冠、中央纪年匾、最高一排四窗及其挑篷、竖肋和凹板。',
          dimensions='归一展示尺度。匾宽取四个模型单位，模型不含实测建筑米标。',
          photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,url=PHOTO_SOURCE,license_url=LICENSE_URL,
          geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
          attribution='上海市房屋管理局第五批优秀历史建筑5F002、人民网上海频道2015年报道、2017年刊载的2016年摄建筑组照。',
          copyright='Original exhibit geometry and procedural facing under MIT. No reference photograph is embedded.')
PALETTE={**crown_masonry.PALETTE,**crown_window_sashes.PALETTE,**dated_cartouche.PALETTE}
def load_layout():
    return json.loads((SOURCE.parent/'measurements/crown-layout.json').read_bytes())
def add_building(builder,lod=False):
    layout=load_layout()
    crown_masonry.add_masonry(builder,lod,layout)
    crown_window_sashes.add_crown_windows(builder,lod,layout['openings'])
    crown_window_sashes.add_crown_brick_panels(builder,lod,layout['panels'])
    dated_cartouche.add_cartouche(builder,lod,layout)
def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender')
    args,extra=parser.parse_known_args()
    if args.output:
        if extra:parser.error('Unknown arguments: '+' '.join(extra))
        builder=CrownBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META);return
    if args.lod:parser.error('--lod requires --output')
    from asset_rights import retain_metadata,licensed_writer
    os.environ['TANGGU_CROWN_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=CrownBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
    pack.build(SOURCE,META,PALETTE,add_building)
if __name__=='__main__':main()
