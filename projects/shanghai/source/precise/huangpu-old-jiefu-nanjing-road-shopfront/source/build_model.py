"""Construct the two street fronts and rounded northwest corner of the Old Jiefu store."""
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
from corner_crown import add_corner_crown,PALETTE as CROWN
from paint import apply_metric_uv
from shopfront import shop,upper,PALETTE as STREET
from nanjing_steel_windows import PALETTE as WINDOWS
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE

META=dict(id='huangpu-old-jiefu-nanjing-road-shopfront',name='老介福北西街面与退台砖塔冠',
          viewer_page='old-jiefu-nanjing-road-shopfront.html',heritage_group='5A040',
          source_period='2024年4月23日两张署名原照，与2014、2018年临街照片对照',
          scope='南京东路257号北立面、河南中路西立面及两街转角的店面、铁窗裙、石檐和砖砌塔冠。三维不包含后侧邻楼。',
          geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
          photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
          copyright='Reconstructed architectural geometry from photographs by Chainwit., Antigng and Livelikerw. CC BY-SA 4.0. Original procedural facing-brick texture MIT.',
          attribution='Chainwit., 257 Nanjing East Road, Shanghai, IMG 01/02 (2024), CC BY 4.0; Antigng, Old Jiefu Building (2018), CC BY-SA 4.0; Livelikerw, Forever 21 (2014), CC BY-SA 3.0. See SOURCES-LICENSE.md.')
PALETTE={**STREET,**WINDOWS,**CROWN,MATERIAL:dict(color=[1.,1.,1.],roughness=.9,texture=str(TEXTURE))}

def add_building(builder,lod):
    shop(builder,lod)
    upper(builder,lod)
    add_corner_crown(builder,lod)
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
        os.environ['OLD_JIEFU_STOREFRONT_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
