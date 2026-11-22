"""Make the two separately numbered entrances and upper windows at Wujin Road Lane 225."""
import argparse,json,os,sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'));import package_architectural_model as pack
sys.path.insert(0,str(SOURCE))
from brick_builder import WujinBuilder
import entrance_wall,paired_entrances,upper_sashes
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
MID='hongkou-wujin-225-paired-residential-entrances'
META=dict(id=MID,name='武进路225弄9、11号双券宅门',viewer_page='wujin-225-paired-residential-entrances.html',heritage_group='5F010',
    scope='以门上号牌辨认的两座宅门、院内砖墙、二层两扇窗与可见檐口。',
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,
    photos_embedded=False,url=PHOTO_SOURCE,dimensions='以9号门横档净宽1.43个模型单位确定展示比例。实体砖皮和现场绝对标高有待测量。',
    attribution='高参88，2015年7月24日《武进路225弄9号、11号一对经典的双门》；上海市房屋管理局第五批5F010。',
    copyright='Original architecture meshes and procedural textures MIT. The referenced photographs are credited to their respective authors. No photographic pixels are embedded.')
PALETTE={**entrance_wall.PALETTE,**paired_entrances.PALETTE,**upper_sashes.PALETTE}
def add_building(b,lod=False):
    entrance_wall.add_wall(b,lod)
    paired_entrances.add_entrances(b,lod)
    upper_sashes.add_upper_sashes(b,lod)
def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender');args,extra=parser.parse_known_args()
    if args.output:
        if extra:parser.error('Unexpected model arguments '+str(extra))
        b=WujinBuilder(PALETTE);add_building(b,args.lod);b.save(args.output,META);return
    if args.lod:parser.error('--lod requires --output')
    from asset_rights import retain_metadata,licensed_writer
    os.environ['WUJIN_DOORS_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=WujinBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META);pack.build(SOURCE,META,PALETTE,add_building)
if __name__=='__main__':main()
