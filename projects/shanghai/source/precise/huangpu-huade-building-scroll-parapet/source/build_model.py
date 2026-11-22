"""The two pierced parapet panels and studded soffits at 620 Middle Sichuan Road."""
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


from parapet import (rail, LIP, RETURN, SCROLL, NARROW, KEY, FLOOR, DISC, EDGE, BAR, PILASTER)
from paint import TEXTURE,apply_metric_uv
from material_names import MATERIAL
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='huangpu-huade-building-scroll-parapet',name='华德大楼四川中路立面双卷草栏板与圆饰托板',
    heritage_group='5A008',viewer_page='huade-building-scroll-parapet.html',
    scope='四川中路620号沿街连续露台的两组透空卷草栏板及其悬挑底面的两块九圆饰托板。',
    source_period='Antigng摄于2015年7月20日',geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,
    photos_embedded=False,photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
    copyright='Geometry CC BY-SA 4.0. Photograph by Antigng, 20 July 2015: '+PHOTO_SOURCE+' . '+LICENSE_URL,
    attribution='After the paired parapet in Antigng’s photograph of the Huade Building. Geometry CC BY-SA 4.0. Original procedural limestone grain and code MIT.')
def pigment(rgb,rough=.85,metal=0.):
    c=np.asarray(rgb)/255.
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={MATERIAL:dict(color=[1.,1.,1.],roughness=.95,texture=str(TEXTURE)),
    LIP:pigment([221,213,194]),RETURN:pigment([171,161,141]),SCROLL:pigment([227,221,202]),
    NARROW:pigment([185,175,152]),KEY:pigment([210,202,183]),FLOOR:pigment([180,172,152]),
    DISC:pigment([190,183,164]),EDGE:pigment([155,149,132]),BAR:pigment([67,64,56],.71,.23),PILASTER:pigment([208,201,183])}
def add_building(builder,lod):
    rail(builder,lod)
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
        os.environ['HUADE_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder
        pack.retain_metadata=retain_metadata
        pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
