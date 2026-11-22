"""Build the upper street elevation of the historical Cheng residence."""
import argparse
import os
from pathlib import Path
import sys

SOURCE=Path(__file__).absolute().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from repeat_materials import RepeatingBuilder
import street_balcony, central_tablet, historic_window_front
from finish_uv import metric_uv, map_return_faces
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='jingan-cheng-family-residence-historic-balcony',name='程氏住宅旧照中的临街花栏、折面长窗与切角石额',viewer_page='cheng-family-residence-historic-balcony.html',heritage_group='5B033',
    scope='南京西路1550号程氏住宅旧照所见二层临街装饰。以历史门楼、长窗与切角石额为限，两张旧刊本来自同次拍摄；尺度以栏身高约0.96米为基准。',
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
    attribution='历史门楼照片见《档案春秋》；高参88的2018年街面照片用于核对保留下来的装饰尺度。两刊旧照的色调只支持相对明暗。',copyright='Original reconstruction and procedural materials licensed under MIT. The reference photographs are credited separately.')
PALETTE={**historic_window_front.PALETTE,**central_tablet.PALETTE,**street_balcony.PALETTE}
def add_building(builder,lod):
    historic_window_front.add_historic_front(builder,lod)
    central_tablet.add_central_tablet(builder,lod)
    street_balcony.add_street_balcony(builder,lod)
    for part in builder.parts:
        part['label']=part['label'].replace('Cheng historic balcony | ','Balcony | ').replace('projecting bay parapet around pierced crown','parapet around pierced crown')
        if part['material'] in (historic_window_front.WALL,historic_window_front.STONE):
            metric_uv(part,.73,.67)
        elif part['material'] in (central_tablet.FACE,central_tablet.HOOD):
            map_return_faces(part,.65)
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        builder=RepeatingBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['CHENG_HISTORIC_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=RepeatingBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
