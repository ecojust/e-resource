"""Build the surveyed southern entrance and its two adjoining Rongkang Villas street houses."""
from pathlib import Path
import argparse,os,sys
SOURCE=Path(__file__).resolve().parent
PROJECT=next((p for p in SOURCE.parents if(p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(SOURCE))
from repeat_materials import RepeatingBuilder
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
import street_masonry as walls
import rongkang_window_sashes as sashes
import lane_head as head
import lane_piers_gate as gate
import shop_signs as signs

META=dict(id='jingan-rongkang-villas-changshu-road-lane-front',
          name='荣康别墅常熟路南弄门及两侧街屋',viewer_page='rongkang-villas-changshu-road-lane-front.html',heritage_group='5B061',
          scope='南弄门、收拢铁扇、两侧街屋和有影像依据的三段回墙，含18扇楼上窗、6处街面门窗、4块横招、两列门柱字和118号小门牌。',
          photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
          url='https://commons.wikimedia.org/wiki/File:%E8%8D%A3%E5%BA%B7%E5%88%AB%E5%A2%85.jpg',
          attribution='Antigng 2017-08-19高分辨率原照片、2015至2021年常熟路街景以及上海市第五批优秀历史建筑名录5B061。',
          copyright='Original architectural mesh and procedural textures MIT. Photo-traced signs CC BY-SA 4.0. Noto Sans CJK SC Bold substitute glyphs under SIL OFL 1.1. Reference photography is not embedded in the model.')
PALETTE={**walls.PALETTE,**sashes.PALETTE,**head.PALETTE,**gate.PALETTE,**signs.PALETTE}
def add_building(builder,lod=False):
    walls.add_masonry(builder,lod)
    head.add_lane_head(builder,lod)
    gate.add_lane_piers_gate(builder,lod)
    sashes.add_street_windows(builder,lod)
    signs.add_shop_signs(builder,lod,walls.PANELS)
    signs.add_south_pier_words(builder,lod)
def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender');args,extra=parser.parse_known_args()
    if args.output:
        if extra:parser.error('Unknown model arguments: '+' '.join(extra))
        builder=RepeatingBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META);return
    if args.lod:parser.error('--lod requires --output')
    from asset_rights import retain_metadata,licensed_writer
    os.environ['RONGKANG_VILLAS_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=RepeatingBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
    pack.build(SOURCE,META,PALETTE,add_building)
if __name__=='__main__':main()
