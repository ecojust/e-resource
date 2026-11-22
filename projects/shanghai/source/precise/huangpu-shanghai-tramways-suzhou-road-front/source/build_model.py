"""Build the four-pilaster street elevation at 185 South Suzhou Road."""
import argparse,hashlib,json,os,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

SOURCE=Path(__file__).absolute().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:
    PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as TexturedBuilder


from frontage import add_frontage, PALETTE as FRONT
from balcony import add_balcony
from measured_wreaths import add_wreaths, PALETTE as WREATH
from doorway import add_doorway, PALETTE as DOOR
from material_names import MATERIAL
from paint import TEXTURE,apply_metric_uv
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
from asset_rights import licensed_writer,retain_metadata
META=dict(id='huangpu-shanghai-tramways-suzhou-road-front',name='英商上海电车公司大楼临河立面与柱廊入口',heritage_group='5A024',
          viewer_page='shanghai-tramways-suzhou-road-front.html',scope='南苏州路185号主街面、四条花环壁柱、凸弧阳台、底层三根可见圆柱与内退券门，以及照片右端短折角。',
          source_period='2015年7月20日署名街照',geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
          photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
          copyright='Geometry CC BY-SA 4.0. Source photograph by Antigng. Original code and procedural finish MIT.',
          attribution='Architectural geometry based on the Shanghai Tramways Building photograph by Antigng, 20 July 2015, Wikimedia Commons, CC BY-SA 4.0. The photograph is referenced separately.')
PALETTE={MATERIAL:dict(color=[1.,1.,1.],roughness=.95,texture=str(TEXTURE)),**FRONT,**WREATH,**DOOR}
def add_building(builder,lod):
    add_frontage(builder,lod)
    add_balcony(builder,lod)
    add_doorway(builder,lod)
    add_wreaths(builder,lod,-.21)
    apply_metric_uv(builder)
AggregateBuilder=TexturedBuilder
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['TRAMWAYS_FRONTAGE_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder
        pack.retain_metadata=retain_metadata
        pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
