"""Build the Shaanxi Road entrance and southeast brick tower of Grace Church."""
from pathlib import Path
import argparse
import os
import sys
SRC=Path(__file__).resolve().parent
sys.path.insert(0,str(SRC.parents[3]/'tools'))
from package_architectural_model import build
from church_front import PALETTE,building
ID='jingan-grace-church-street-front'
SCOPE='陕西北路375号现址，依据2006、2013、2026年的街面及静安博物馆归档正面制作两扇可辨入口、三窗前厅和东南砖塔。前院门柱、沿街设备屋、礼堂后部、其他小堂与369号宋氏住宅另列。'
META={'id':ID,'name':'怀恩堂陕西北路入口与东南角砖塔','status':'original-photo-informed-exterior','viewer_page':'grace-church-street-front.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':'街面按当前地块临陕西北路的短边约12.24米标定；砖塔与尖顶高度、浅进深和遮挡处由归档正面、斜视照片估算。','interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json','coordinate_convention':'Positive X runs toward the north end of the street elevation as seen from the road. Positive Y runs into the western part of the parcel, Z up.','copyright':'Original geometry and materials, MIT. Photographs are external references.'}
if __name__=='__main__':
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['GRACE_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SRC/'blender_preview.py')]
    build(SRC,META,PALETTE,building)
