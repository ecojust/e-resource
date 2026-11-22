"""Build the former Bank of Communications warehouse along Guangfu Road."""
from pathlib import Path
import argparse,json,os,sys
SOURCE=Path(__file__).resolve().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(SOURCE))
from river_builder import RiverBuilder
import river_masonry as stone
import south_entrance as entrance
import south_passage as passage
import roof_terrace as terrace
import east_wall_sign as east_sign
from rights import GEOMETRY_LICENSE, PHOTO_AUTHOR, PHOTO_SOURCE, LICENSE_URL, TEXTURE_LICENSE
import warehouse_window_sashes as windows

SLUG='jingan-bank-of-communications-warehouse-guangfu-riverfront'
META=dict(id=SLUG,name='原交通银行仓库光复路临河立面',viewer_page='bank-of-communications-warehouse-guangfu-riverfront.html',
    heritage_group='5H003',scope='光复路195号向苏州河的四层折弧立面、中央门楼、69处窗与商铺开口、两端回墙、南侧露台及中央车道首段。',
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,
    license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,
    photos_embedded=False,url='https://sh.people.com.cn/n2/2026/0604/c134768-41601453.html',
    attribution='上海市房屋管理局第五批优秀历史建筑5H003、1934年交行通信、1947年电话簿、修缮团队的平面与现代临河照片。',
    copyright='Original measured architectural geometry and procedural textures under MIT. Restored signs, names and brand identifiers depict the existing site. Original artwork and marks belong to their respective owners. Reference photographs and architectural drawings are not embedded.')
PALETTE={**stone.PALETTE,**entrance.PALETTE,**windows.PALETTE,**passage.PALETTE,**terrace.PALETTE,**east_sign.PALETTE}
PALETTE[entrance.STONE]={**PALETTE[entrance.STONE],
    'color':[.92,.92,.92],'texture':str(SOURCE/'guangfu-washed-aggregate.jpg')}
def load_layout():
    return json.loads((SOURCE.parent/'measurements/riverfront-layout.json').read_bytes())

def add_building(builder,lod=False):
    layout=load_layout()
    stone.add_wings(builder,lod,layout)
    entrance.add_south_entrance(builder,lod,layout['frame'])
    windows.add_warehouse_windows(builder,lod,layout)
    windows.add_west_return_windows(builder,lod,layout)
    passage.add_passage(builder,lod,layout)
    terrace.add_terrace(builder,lod,layout)
    east_sign.add_east_wall_sign(builder,lod,layout)

def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender')
    args,extra=parser.parse_known_args()
    if args.output:
        if extra:parser.error('Unknown model arguments: '+' '.join(extra))
        b=RiverBuilder(PALETTE);add_building(b,args.lod);b.save(args.output,META);return
    if args.lod:parser.error('--lod requires --output')
    from asset_rights import retain_metadata,licensed_writer
    os.environ['GUANGFU_WAREHOUSE_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=RiverBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
    pack.build(SOURCE,META,PALETTE,add_building)
if __name__=='__main__':main()
