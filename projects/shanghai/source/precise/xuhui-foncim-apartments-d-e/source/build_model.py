"""Build the two residential blocks and the open garden passage at Gao'an Road Lane 78."""
from pathlib import Path
import argparse,json,math,os,sys
import numpy as np

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as package
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
from striped_render import MATERIAL,TEXTURE
from north_block import NORTH_PALETTE,build_north
from south_block import SOUTH_PALETTE,build_south
from courtyard import COURT_PALETTE,build_court
from garden_ground import GARDEN_PALETTE

ID='xuhui-foncim-apartments-d-e'
META=dict(id=ID,name='方建公寓D、E楼与庭院敞廊',viewer_page='foncim-apartments-d-e.html',
          heritage_group='4D040',heritage_address='高安路78弄1–3号、建国西路641–645号',
          scope='五层北楼D、四层南楼E和连接两者的有顶敞廊。')
PALETTE={**NORTH_PALETTE,**SOUTH_PALETTE,**COURT_PALETTE,**GARDEN_PALETTE,
         MATERIAL:dict(color=[1.,1.,1.],roughness=.91,texture=str(TEXTURE))}
SITE=json.loads((SOURCE.parent/'measurements/site-frame.json').read_bytes())

def add_building(b,lod):
    build_north(b,lod)
    begin=len(b.parts)
    build_south(b,lod)
    frame=SITE['old_floorplates']['E']
    angle=math.radians(frame['local_rotation_degrees']);cos=math.cos(angle);sin=math.sin(angle)
    offset=np.array(frame['local_origin_xy'])
    rotation=np.array([[cos,sin],[-sin,cos]])
    for part in b.parts[begin:]:
        v=np.asarray(part['vertices'])
        v[:,:2]=v[:,:2]@rotation+offset
        part['vertices']=v.tolist()
    far_entry=np.array([0.,-1.64])@rotation+offset
    build_court(b,lod,far_entry)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('unexpected arguments for a raw export: '+' '.join(rest))
        builder=AggregateBuilder(PALETTE);add_building(builder,args.lod)
        builder.save(args.output,META)
    else:
        os.environ['FONCIM_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'native_blender.py')]
        package.Builder=AggregateBuilder
        package.build(SOURCE,META,PALETTE,add_building)
