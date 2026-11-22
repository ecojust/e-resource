"""Build the west street elevation of the residence photographed at 195 Shaanxi Road South."""
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

from court_wall import PALETTE as COURT,add_boundary
from house_fabric import PALETTE as HOUSE,add_house
from west_upper_windows import PALETTE as WINDOWS,add_windows
from south_loggia import PALETTE as LOGGIA,add_south_loggia
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id="huangpu-shaanxi-191-197-residential-front",name="陕西南路195号住宅与南端叠廊",
 viewer_page="shaanxi-191-197-residential-front.html",heritage_group="5A052",source_period="2018年6月10日实照、2015及2017年沿街观察",
 scope="名录中陕西南路191至197号住宅的195号实照。复原朝街两层主墙、成对格窗、前瓦坡与南端上下叠廊。",
 geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,photo_author=PHOTO_AUTHOR,
 photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,copyright="Geometry derived from WQL, Shaanxi South Road No. 195, CC BY-SA 4.0. Original procedural sand render MIT.",
 attribution="WQL, 陕西南路195号, Wikimedia Commons, 2018-06-10, CC BY-SA 4.0.")
PALETTE={**HOUSE,**COURT,**WINDOWS,**LOGGIA,MATERIAL:dict(color=[1.,1.,1.],roughness=.95,texture=str(TEXTURE))}
def add_building(builder,lod):
    add_house(builder,lod)
    add_boundary(builder,lod)
    add_windows(builder,lod)
    add_south_loggia(builder,lod)
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
        os.environ['SHAANXI_RESIDENCE_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
