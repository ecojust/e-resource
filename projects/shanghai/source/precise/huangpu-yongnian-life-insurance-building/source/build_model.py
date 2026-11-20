"""Package the original local bank exterior at 93 Guangdong Road."""
from pathlib import Path
import sys
import os
import argparse
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from yongnian_geometry import PALETTE,add_building

ID='huangpu-yongnian-life-insurance-building'
SCOPE='广东路93号永年人寿保险公司街角营业楼。以市地方志、2011年街照及航片复原东北方门、磨光红花岗石柱、双街券窗、连续两层爱奥尼克柱和两型窗楣。背墙、局部第四层和标高按现有外部资料估计。'
META={'id':ID,'name':'永年人寿保险公司大楼（广东路93号）','status':'original-photo-informed-exterior','viewer_page':'yongnian-life.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Metres, +X 17.85 degrees north of east. The main portal faces northeast towards the intersection. Map heading −17.85 degrees.','copyright':'Original geometry MIT. No photographs or prior models embedded.'}
if __name__=='__main__':
    # Preserve the packager's --blender option and its argv, including a
    # system-specific launcher, while setting our local camera before save.
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['YONGNIAN_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
