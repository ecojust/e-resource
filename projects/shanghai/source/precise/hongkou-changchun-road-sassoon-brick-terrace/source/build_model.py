"""Make the eight photographed north-facing window axes of the Changchun Road terrace."""
import argparse,json,os,sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'));import package_architectural_model as pack
sys.path.insert(0,str(SOURCE))
from brick_builder import TerraceBuilder
import terrace_wall,upper_windows,sassoon_roof_windows,terrace_roof,front_enclosure,frontage_fittings
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
MID='hongkou-changchun-road-sassoon-brick-terrace'
META=dict(id=MID,name='长春路沙逊楼群北立面八开间',viewer_page='changchun-road-sassoon-brick-terrace.html',heritage_group='5F014',
    scope='长春路北向街面照片可定位的连续八开间、砖券与红白窗间、屋顶上可见的两对山花及其间屋窗，沿街院墙与街面。',
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,
    photos_embedded=False,url=PHOTO_SOURCE,dimensions='依据高参88摄于2015年的原片和虹口区刊载正照。七处水平砖缝校约为每皮0.063个模型单位，属图估尺寸。',
    attribution='上海虹口，长春路街道影像；高参88，2015年4月25日拍摄。上海市房屋管理局第五批5F014。',
    copyright='Original geometry and procedural textures MIT. Reference photographs remain with the respective photographers and publishers. No third-party photo pixels are embedded.')
PALETTE={**terrace_wall.PALETTE,**upper_windows.PALETTE,**sassoon_roof_windows.PALETTE,**terrace_roof.PALETTE,**front_enclosure.PALETTE,**frontage_fittings.PALETTE}
def add_building(b,lod=False):
    terrace_wall.add_front(b,lod)
    upper_windows.add_windows(b,lod)
    terrace_roof.add_roof(b,lod)
    sassoon_roof_windows.add_roof_windows(b,lod)
    front_enclosure.add_enclosure(b,lod)
def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender');args,extra=parser.parse_known_args()
    if args.output:
        if extra:parser.error('Unexpected model arguments '+str(extra))
        b=TerraceBuilder(PALETTE);add_building(b,args.lod);b.save(args.output,META);return
    if args.lod:parser.error('--lod requires --output')
    from asset_rights import retain_metadata,licensed_writer
    os.environ['CHANGCHUN_TERRACE_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=TerraceBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META);pack.build(SOURCE,META,PALETTE,add_building)
if __name__=='__main__':main()
