"""Rebuild the photograph-bound central portal and carved stone hood."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from entrance import PALETTE,add_building

ID='huangpu-hengfeng-building-entrance'
SCOPE='江西中路450–454号恒丰大楼原西立面中央入口。照片可辨题名、双门柱、两根通高槽柱、卷叶门罩和上方两对窗。'
META={'id':ID,'name':'恒丰大楼江西中路题名门罩与柱列','viewer_page':'hengfeng-building-entrance.html','scope':SCOPE,'model_scope_zh':SCOPE,'reference_height_m':13.65,'status':'original-photo-informed-exterior','estimated':'西墙中段沿街宽8.36米、高13.65米，参考全景和原地块定位。进深、字形、雕花断面和门内阴影均按照片估算。','coordinate_convention':'Right-hand Z up, X south along the frontage, Y into the building. Metres.','source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'copyright':'Original geometry and original procedural stone tile. The four 3D letters use a renamed subset of the SIL Open Font License Noto Serif CJK TC typeface. The photos are referenced only.'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,remainder=parser.parse_known_args()
    os.environ['HENGFENG_BLENDER']=options.blender
    sys.argv[1:]=[*remainder,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
