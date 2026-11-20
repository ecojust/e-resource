"""Build the courtyard elevation of the McTyeire Social Hall."""
from pathlib import Path
import argparse
import os
import sys
SRC=Path(__file__).resolve().parent
sys.path.insert(0,str(SRC.parents[3]/'tools'))
from package_architectural_model import build
from social_hall import PALETTE,building
ID='changning-mctyeire-east-building'
SCOPE='江苏路155号东楼五一楼的庭院正面，以2017年照片制作两组六孔拱廊、双排窗、红瓦老虎窗及中央山墙门廊。两端伸出的翼、北侧房间与独立的五四楼继续保留底图。'
META={'id':ID,'name':'中西女中东楼（五一楼）院落立面','status':'original-photo-informed-exterior','viewer_page':'mctyeire-east-building.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':'中央突出段底图宽约20.3米，整段院面约70.7米。高程、屋面及门廊进深按2017年照片估计。','interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json','coordinate_convention':'Local +X southeast along the courtyard front and positive Y northeast into the wall. Z is up.','copyright':'Original geometry and materials, MIT. Photographs are external references.'}
if __name__=='__main__':
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['MCTYEIRE_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SRC/'blender_preview.py')]
    build(SRC,META,PALETTE,building)
