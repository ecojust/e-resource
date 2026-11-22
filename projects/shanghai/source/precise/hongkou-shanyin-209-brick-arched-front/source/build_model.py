"""Create the garden front and tiled front roof of house 3 at Shanyin Road Lane 209."""
import argparse,json,os,sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'));import package_architectural_model as pack
sys.path.insert(0,str(SOURCE))
from brick_builder import ShanyinBuilder
import frontage,shanyin_arches,ground_arcade,roof_dormers,tiled_roof,garden_fittings
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
MID='hongkou-shanyin-209-brick-arched-front'
META=dict(id=MID,name='山阴路209弄3号三券花园正面',viewer_page='shanyin-209-brick-arched-front.html',heritage_group='5F006',
    scope='3号的两层三道砖券、花园廊和台阶、花架、两座老虎窗及前方红瓦屋坡。',
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,
    photos_embedded=False,url=PHOTO_SOURCE,dimensions='基于墙面砖皮与双幅照片的展示比例，原砖尺寸及后瓦面进深待测。',
    attribution='Fayhoo，2015年4月12日，Shanyinlu 209 Long Zhuzhai.JPG，CC BY-SA 3.0；虹口区历史建筑公开影像；上海市房屋管理局第五批名单5F006。',
    copyright='3D architecture redrawn from Fayhoo’s CC BY-SA 3.0 photograph; geometry CC BY-SA 3.0. Original procedural textures and code MIT. Reference photo pixels are excluded from the GLB.')
PALETTE={**frontage.PALETTE,**ground_arcade.PALETTE,**shanyin_arches.PALETTE,**roof_dormers.PALETTE,**tiled_roof.PALETTE,**garden_fittings.PALETTE}
def load_layout():return json.loads((SOURCE.parent/'measurements/garden-front-layout.json').read_bytes())
def add_building(b,lod=False):
    layout=load_layout()
    frontage.add_frontage(b,lod,layout)
    ground_arcade.add_ground_arcade(b,lod,layout)
    shanyin_arches.add_shanyin_arches(b,lod,layout['upper_openings'])
    garden_fittings.add_fittings(b,lod,layout)
    tiled_roof.add_roof(b,lod,layout)
    roof_dormers.add_dormers(b,lod,layout)
def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender');args,extra=parser.parse_known_args()
    if args.output:
        if extra:parser.error('Unexpected model arguments '+str(extra))
        b=ShanyinBuilder(PALETTE);add_building(b,args.lod);b.save(args.output,META);return
    if args.lod:parser.error('--lod requires --output')
    from asset_rights import retain_metadata,licensed_writer
    os.environ['SHANYIN_GARDEN_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'build_blender_source.py')]
    pack.Builder=ShanyinBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META);pack.build(SOURCE,META,PALETTE,add_building)
if __name__=='__main__':main()
