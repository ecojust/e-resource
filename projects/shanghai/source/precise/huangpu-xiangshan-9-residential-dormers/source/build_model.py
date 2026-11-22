"""Build the documented street frontage of the Xiangshan Road No. 9 residence."""
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

from xiangshan_frontage import PALETTE as FABRIC, add_frontage
from xiangshan_dormers import PALETTE as DORMERS, add_dormers
from courtyard_ironwork import PALETTE as IRONWORK, add_courtyard_boundary
from asset_rights import licensed_writer, retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='huangpu-xiangshan-9-residential-dormers',name='香山路9号住宅临街立面与双山墙老虎窗',viewer_page='xiangshan-9-residential-dormers.html',heritage_group='5A080',source_period='Antigng于2018年7月30日摄，参照2015年冬季街面可辨的建筑构件。',
 scope='临街灰白抹灰墙、五处二层窗、前坡上的两座大小不同的山墙老虎窗、两者间的连窗及前景院墙。地块纵深与树冠遮挡处未作测绘。',
 geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
 copyright='Architecture and observed details derived from the photograph by Antigng, CC BY-SA 4.0. Geometry CC BY-SA 4.0; original procedural mineral render texture MIT.',
 attribution='Antigng, Xiangshan Road No. 9 residence, photograph of 30 July 2018, Wikimedia Commons, CC BY-SA 4.0.')
PALETTE={**FABRIC, **DORMERS, **IRONWORK, MATERIAL:dict(color=[1.,1.,1.],roughness=.91,texture=str(TEXTURE))}
def add_building(builder,lod):
    add_frontage(builder,lod)
    add_dormers(builder,lod)
    add_courtyard_boundary(builder,lod)
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
        os.environ['XIANGSHAN_9_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
