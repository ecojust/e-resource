"""Rebuild the measured part of the three-level waterworks street elevation."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from zili_front import PALETTE,add_building

ID='huangpu-zili-waterworks-office-front'
SCOPE='依据街照重建江西中路464号外墙约11米长的三层片段，含有门牌的砖券门、两侧小券与两排窗、红砖挑齿和灰白层间带。'
META={'id':ID,'name':'自力大楼（英商自来水公司办公楼）江西中路464号券门及上层窗墙','viewer_page':'zili-waterworks-office.html','scope':SCOPE,'model_scope_zh':SCOPE,'reference_height_m':11.25,'status':'original-photo-informed-exterior','estimated':'可见西墙与底图28.12米长边校准，所建片段高11.25米、宽11.32米。高程、壁厚、藏在雨篷后面的窗头均为近似。','coordinate_convention':'Right-hand Z up, X south along the frontage, Y into the building. Metres.','source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'copyright':'Original meshes and original procedural painted brick tile. Source photos referenced only.'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,remainder=parser.parse_known_args()
    os.environ['ZILI_BLENDER']=options.blender
    sys.argv[1:]=[*remainder,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
