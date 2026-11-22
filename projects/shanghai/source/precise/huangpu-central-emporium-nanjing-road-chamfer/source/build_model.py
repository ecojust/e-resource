"""Build Central Emporium’s corner entrance and its upper windows."""
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


from market_front import add_front, PALETTE as MASONRY
from corner_fanlight import add_fanlight, PALETTE as FAN
from fluted_archivolt import add_reeded_archivolt
from street_number import add_street_number, PALETTE as NUMBER
from photo_plane import position
from material_names import MATERIAL
from paint import TEXTURE,apply_metric_uv
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
from asset_rights import licensed_writer,retain_metadata
META=dict(id='huangpu-central-emporium-nanjing-road-chamfer',name='中央商场折角入口、扇灯与三层街窗',
          heritage_group='5A028',viewer_page='central-emporium-nanjing-road-chamfer.html',
          scope='四川中路355号名录所列中央商场的2022年折角入口，铜字与南京东路123号小牌、扇灯、凹槽石券及三层街窗。',
          source_period='2022年8月28日入口，2019年7月11日街角各层相互核证',geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,
          photos_embedded=False,photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
          copyright='Geometry CC BY-SA 4.0. Source photographs by Shwangtianyuan (2022) and Livelikerw (2019). Original code and procedural stone texture MIT.',
          attribution='Geometry and derived measurements based on Wikimedia Commons photographs by Shwangtianyuan (28 August 2022) and Livelikerw (11 July 2019), both CC BY-SA 4.0.')
PALETTE={MATERIAL:dict(color=[1.,1.,1.],roughness=.96,texture=str(TEXTURE)),**MASONRY,**FAN,**NUMBER}
def add_building(builder,lod):
    add_front(builder,lod)
    add_fanlight(builder,lod,position,.088,-.116)
    add_reeded_archivolt(builder,lod,0.)
    add_street_number(builder,lod)
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
        os.environ['CENTRAL_EMPORIUM_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder
        pack.retain_metadata=retain_metadata
        pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
