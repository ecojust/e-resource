"""Make the curved bay, pebble gable and veranda of Gongyuanfang No. 24."""
import argparse,json,os,sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'));import package_architectural_model as pack
sys.path.insert(0,str(SOURCE))
from model_builder import FacadeBuilder
import gable_face,curved_front,bay_windows,upper_balcony,entrance_recess,entrance_steps
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
MID='hongkou-gongyuanfang-24-yefeng-art-society-front'
META=dict(id=MID,name='公园坊24号野风画会旧址南立面',viewer_page='gongyuanfang-24-yefeng-art-society-front.html',heritage_group='5F018',
    scope='以具名两期照片为据复原红砖门券与深门廊、卵石山墙、双层弧窗、第三层敞廊，以及通往弄堂的四级台阶和中央窄坡。',
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,
    photos_embedded=False,url=PHOTO_SOURCE,dimensions='按95处相同墙面特征核对的两张照片及旧红砖灰缝估计尺度。每皮砖暂按0.063米，尚无现场测量。',
    attribution='上海市虹口区、上海学习平台2019年9月16日《上海市优秀历史建筑——公园坊》，2022年3月5日澎湃政务所刊《野风画会旧址》照片；上海市房屋管理局第五批5F018。',
    copyright='Original geometry and procedural textures MIT. Reference photographs remain with the respective photographers and publishers. No third-party photo pixels are embedded.')
PALETTE={**gable_face.PALETTE,**bay_windows.PALETTE,**upper_balcony.PALETTE,**entrance_recess.PALETTE,**entrance_steps.PALETTE}
def add_building(b,lod=False):
    gable_face.add_gable(b,lod)
    curved_front.add_wall(b,lod)
    bay_windows.add_windows(b,lod)
    upper_balcony.add_balcony(b,lod)
    entrance_recess.add_entrance_recess(b,lod)
    entrance_steps.add_steps(b,lod)
def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender');args,extra=parser.parse_known_args()
    if args.output:
        if extra:parser.error('Unexpected model arguments '+str(extra))
        b=FacadeBuilder(PALETTE);add_building(b,args.lod);b.save(args.output,META);return
    if args.lod:parser.error('--lod requires --output')
    from asset_rights import retain_metadata,licensed_writer
    os.environ['GONGYUANFANG_24_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=FacadeBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META);pack.build(SOURCE,META,PALETTE,add_building)
if __name__=='__main__':main()
