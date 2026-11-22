"""Build the north elevation and six-column Ionic portico on Dianchi Road."""
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


sys.path.insert(0,str(SOURCE))
from bank_elevation import north_wall,eastern_side_door,condenser_units,base_and_steps,rear_doors,side_portal,porch_beam,PALETTE as WALL
from ionic_portico import add_ionic_column,PALETTE as COLUMNS
from coffered_soffit import add_coffered_soffit,PALETTE as SOFFIT
from photo_plane import position
from material_names import MATERIAL
from paint import TEXTURE,apply_metric_uv
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
from asset_rights import licensed_writer,retain_metadata

META=dict(id='huangpu-chung-foo-union-bank-dianchi-front',name='中孚银行北立面与爱奥尼柱廊',
    heritage_group='5A036',viewer_page='chung-foo-union-bank-dianchi-front.html',source_period='Fayhoo 登记摄影与2017年4月15日北立面档案照片',
    scope='滇池路103号原中孚银行面向滇池路的北立面与街层柱廊，包括四行窗、六根槽柱、石台和西侧门。建筑后方及105号邻楼未纳入。',
    geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
    copyright='Architectural geometry derived from Zhongfudalou by Fayhoo, CC BY-SA 3.0. Original procedural stone texture MIT. No photograph embedded.',
    attribution='Fayhoo, Zhongfudalou, Wikimedia Commons, CC BY-SA 3.0. 2017-04-15 archival north elevation used for architectural reference.')
PALETTE={MATERIAL:dict(color=[1.,1.,1.],roughness=.92,texture=str(TEXTURE)),**WALL,**COLUMNS,**SOFFIT}

def add_building(builder,lod):
    layout=json.loads((SOURCE.parent/'measurements/north-portico-axes.json').read_bytes())
    rows=layout['axes']
    axes=[row['x_m'] for row in rows]
    axis_y=layout['adopted_axis_y_m']
    bases=[row['z_and_pixels']['base']['z_m'] for row in rows]
    base_z=float(np.median(bases))
    north_wall(builder)
    condenser_units(builder,lod)
    base_and_steps(builder,axes,axis_y,bases)
    rear_doors(builder,-.267)
    eastern_side_door(builder)
    side_portal(builder)
    for n,row in enumerate(rows,1):
        radius=row['radius_m_by_view'].get('close') or row['radius_m_by_view']['wide']
        levels=row['z_and_pixels']
        add_ionic_column(builder,lod,'Ionic '+str(n),row['x_m'],row['y_m'],levels['base']['z_m'],levels['neck']['z_m'],radius,position)
    porch_beam(builder,-5.38,10.38,-4.995,6.62)
    add_coffered_soffit(builder,lod,-5.38,10.38,-4.83,-.267,6.62)
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
        os.environ['CHUNG_FOO_BANK_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder
        pack.retain_metadata=retain_metadata
        pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
