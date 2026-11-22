"""Build the photographed frontage at 131 Beijing East Road."""
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

from marconi_street_fabric import PALETTE as FABRIC,evidence
from marconi_windows import PALETTE as WINDOWS,add_windows
from marconi_arched_portal import PALETTE as PORTAL,add_portal
from period_installations import evidence as add_fittings
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='huangpu-marconi-beijing-east-131-front',name='北京东路131号马可尼公司住宅临街立面',viewer_page='marconi-beijing-east-131-front.html',heritage_group='5A076',source_period='2015、2017年Antigng署名照片，以2017年实见开窗状态为准。',
 scope='北京东路131号门牌、红砖券门、三樘弧头窗、两侧屋檐与两座老虎窗。西侧山墙、相邻宽开间的范围以两幅照片可见边界为限。原2128与129号同廓。',
 geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
 copyright='Architecture and observed details derived from photographs by Antigng, CC BY-SA 4.0. Geometry CC BY-SA 4.0; original procedural grey brick texture MIT.',
 attribution='Antigng, photographs of Beijing East Road 131 from 20 July 2015 and 31 August 2017, Wikimedia Commons, CC BY-SA 4.0.')
PALETTE={**FABRIC,**WINDOWS,**PORTAL,MATERIAL:dict(color=[1.,1.,1.],roughness=.91,texture=str(TEXTURE))}
def add_building(builder,lod):
    evidence(builder,lod);add_windows(builder,lod);add_portal(builder,lod);add_fittings(builder,lod);apply_metric_uv(builder)
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        builder=AggregateBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['MARCONI_131_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
