"""Build the courtyard elevation of the McTyeire Social Hall."""
from pathlib import Path
import argparse,json

import os
import sys
SRC=Path(__file__).resolve().parent
sys.path.insert(0,str(SRC.parents[3]/'tools'))
import package_architectural_model as architectural_package
from social_hall import PALETTE,building
ID='changning-mctyeire-east-building'
SCOPE='江苏路155号东楼五一楼的草坪院面，包括中央山墙门廊、前廊，以及东南折返翼已见的17处窗、两根落水管及屋面采光窗。南端树后、西北翼与后排房间保留旧地图体量。'
META={'id':ID,'name':'中西女中东楼（五一楼）院落立面','status':'original-photo-informed-exterior','viewer_page':'mctyeire-east-building.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':'中央突出段底图宽约20.3米，整段院面约70.7米。高程、屋面及门廊进深按2017年照片估计。','interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json','coordinate_convention':'Local +X southeast along the courtyard front and positive Y northeast into the wall. Z is up.','copyright':'Original geometry and materials, MIT. Photographs are external references.'}
HERE=SRC
PROJECT=SRC.parents[3]
from lawn_builder import LawnBuilder
import lawn_finishes
PALETTE={**PALETTE,**lawn_finishes.PALETTE}
META.update(heritage_id='sh-historic-b2-070',official_id='2M008',geometry_license='MIT',texture_license='MIT',photos_embedded=False,
            photo_source='https://commons.wikimedia.org/wiki/File:Shanghai_No._3_Girls%27_High_School,_Five-One_lecture_hall_panorama.jpg',camera_views=json.loads((HERE/'cameras.json').read_bytes()))

def add_building(b,lod=False):
    building(b,lod)

if __name__=='__main__':
    if '--output' in sys.argv:
        cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',type=Path,required=True);cli.add_argument('--lod',action='store_true');a=cli.parse_args()
        builder=LawnBuilder(PALETTE);building(builder,a.lod);builder.save(a.output,META)
    else:
        launch=argparse.ArgumentParser(add_help=False)
        launch.add_argument('--blender',default='blender')
        options,remaining=launch.parse_known_args()
        os.environ['MCTYEIRE_MODEL_BLENDER']=options.blender
        sys.argv[1:]=[*remaining,'--blender',str(SRC/'blender_preview.py')]
        architectural_package.Builder=LawnBuilder
        architectural_package.build(SRC,META,PALETTE,building)
