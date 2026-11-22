"""Build the brick exhibition hall converted from the canteen at Yimin No. 1 Food Factory."""
import argparse,os,sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(SOURCE))
from model_builder import HallBuilder
import hall_masonry as masonry
import hall_windows,hall_roof
from hall_coordinates import WIDTH,LENGTH
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE

MID='hongkou-yimin-food-factory-former-canteen'
META=dict(id=MID,name='益民食品一厂旧食堂改建展厅',viewer_page='yimin-food-factory-former-canteen.html',heritage_group='5F022',
    scope='香烟桥路13号院内旧食堂改建的两层灰砖展厅，取西北和东南两处四开间端墙、临水与沿街的长墙及两端露出小山花的四坡瓦顶。',
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,license_url=LICENSE_URL,
    photos_embedded=False,url=PHOTO_SOURCE,dimensions='依航片、城市楼廓及独立拍摄的三张实地照片估计。建筑轮廓近56.5×18.7米，未作现场测量。',
    attribution='上海市房屋管理局第五批5F022，虹口区企业服务云2018年展馆介绍和外景照，Coolmanjackey于2013年7月30日摄西北端、香烟桥路分期街景及院落航片。',
    copyright='Original geometry and procedural finishes MIT. Source images retain the rights of their photographers and publishers. No third-party photograph is embedded.')
PALETTE={**masonry.PALETTE,**hall_windows.PALETTE,**hall_roof.PALETTE}

def add_building(b,lod=False):
    for face,rows in masonry.LAYOUT['faces'].items():masonry.add_facade(b,face,rows,lod)
    b.box((WIDTH/2,LENGTH/2,.033),(WIDTH-.46,LENGTH-.46,.066),masonry.BASE,label='Ground floor threshold slab')
    for y in [17.41,40.58]:masonry.downpipe(b,'canal',LENGTH-y,masonry.LAYOUT['eave'],lod)
    masonry.downpipe(b,'northwest',-.103,masonry.LAYOUT['eave'],lod)
    masonry.downpipe(b,'northwest',WIDTH-.2,masonry.LAYOUT['eave'],lod)
    hall_roof.add_roof(b,lod)

def main():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender');args,extra=parser.parse_known_args()
    if args.output:
        if extra:parser.error('Unexpected model arguments '+str(extra))
        b=HallBuilder(PALETTE);add_building(b,args.lod);b.save(args.output,META);return
    if args.lod:parser.error('--lod requires --output')
    from asset_rights import retain_metadata,licensed_writer
    os.environ['YIMIN_CANTEEN_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=HallBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
    pack.build(SOURCE,META,PALETTE,add_building)
if __name__=='__main__':main()
