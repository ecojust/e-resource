"""Build the Art Deco bank and stepped tower at 143 Yanan East Road."""
from pathlib import Path
import sys
import os
import argparse
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from chungwei_geometry import PALETTE,add_building

ID='huangpu-chung-wei-bank-building'
SCOPE='延安东路143号原中汇银行大楼的现状外观。河南南路的长窗带、南侧短边、北端退台红砖塔及顶部金属桅杆按2015、2024两组现照、地方志和航片估计。后期填平的中庭留作平屋顶。'
META={'id':ID,'name':'中汇大楼（原中汇银行大楼）','status':'original-photo-informed-exterior','viewer_page':'chung-wei-bank.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Metres. +X points 11.402 degrees north of east. The map heading is −11.402 degrees. The tower rises over the north entrance on Yanan East Road.','copyright':'Original geometry MIT. No images or historical meshes embedded.'}
if __name__=='__main__':
    # Preserve the packager's --blender option and its argv, including a
    # system-specific launcher, while setting our local camera before save.
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['CHUNGWEI_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
