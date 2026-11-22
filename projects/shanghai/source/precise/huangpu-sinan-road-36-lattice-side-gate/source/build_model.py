"""The two gate piers, fixed iron bay and enamel side-gate plaque at 36 Sinan Road."""
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


from piers import add_piers,add_notice,attach_outer_ends,NOTICE,NOTICE_EDGE,LIGHT,SHADOW,TILE,BASE,JOINT,CAP
from address_plaque import add_plaque,GREEN,WHITE,FINE,EDGE
from iron_panel import add_iron,PALETTE as IRON_PALETTE
from paint import TEXTURE,apply_metric_uv
from material_names import MATERIAL
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='huangpu-sinan-road-36-lattice-side-gate',name='思南路36号边门的错台门柱与几何铁栏',
    heritage_group='5A012',viewer_page='sinan-road-36-lattice-side-gate.html',
    scope='思南路36号边门旁的两根错台门柱、柱间固定铁栏与低墙，以及右柱的绿色搪瓷门牌。',
    source_period='Antigng摄于2018年7月30日',geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,
    photos_embedded=False,photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
    copyright='Geometry and traced sign CC BY-SA 4.0. Antigng, 30 July 2018. '+PHOTO_SOURCE+' . '+LICENSE_URL,
    attribution='Model and enamel lettering measured from Antigng’s 2018 photograph of 36 Sinan Road. Geometry CC BY-SA 4.0. Procedural plaster texture and code MIT.')
def pigment(rgb,rough=.85,metal=0.):
    c=np.asarray(rgb)/255.
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={MATERIAL:dict(color=[1.,1.,1.],roughness=.94,texture=str(TEXTURE)),LIGHT:pigment([206,201,175]),SHADOW:pigment([51,51,43]),TILE:pigment([46,51,48],.48),BASE:pigment([139,145,135]),JOINT:pigment([103,107,98]),CAP:pigment([196,190,166]),GREEN:pigment([1,57,42],.49,.08),WHITE:pigment([154,175,151],.55),FINE:pigment([193,204,177],.55),EDGE:pigment([37,80,62],.53,.09),NOTICE:pigment([174,178,161]),NOTICE_EDGE:pigment([105,95,78]),**IRON_PALETTE}
def add_building(builder,lod):
    add_piers(builder,lod)
    add_iron(builder,lod)
    attach_outer_ends(builder,lod)
    add_notice(builder,lod)
    add_plaque(builder,lod)
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
        os.environ['SINAN_SIDE_GATE_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder
        pack.retain_metadata=retain_metadata
        pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
