"""Build two separately photographed entries at nos. 212 and 244 Nanchang Road."""
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
from aggregate_mesh import AggregateBuilder
from material_names import MATERIAL,TEXTURE
from paint import apply_metric_uv

from historic_facade import PALETTE as FACADE,add_facade
from historic_roof_ornament import PALETTE as CREST,add_ornament
from historic_central_glazing import PALETTE as CENTRAL,add_central_glazing
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='huangpu-ruijin-207-historic-roof-ornament',name='瑞金二路207号公董局医学化验所历史立面',
 viewer_page='ruijin-207-historic-roof-ornament.html',heritage_group='5A072',source_period='1930年代两张历史照片',
 scope='按两张历史照片还原瑞金二路207号公董局医学化验所的九跨长立面、端部玻璃带、可见短侧翼、中央深色窗和屋顶构件。以3.5米估算层高，原有地块保持原样。',
 geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
 copyright='Original geometry and procedural render texture. Historical photographs are cited as measurement references. No historical photograph pixels are included.',
 attribution='Historical Photographs of China, University of Bristol, Ro-s018, photographed by Malcolm Rosholt circa 1938. A second historical view records the former municipal laboratory before its institutional reorganization.')
PALETTE={**FACADE,**CREST,**CENTRAL,MATERIAL:dict(color=[1.,1.,1.],roughness=.90,texture=str(TEXTURE))}
def add_building(builder,lod):
    add_facade(builder,lod)
    add_ornament(builder,lod)
    add_central_glazing(builder,lod)
    apply_metric_uv(builder)
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        builder=AggregateBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['RUIJIN_HISTORIC_PUBLIC_LAB_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
