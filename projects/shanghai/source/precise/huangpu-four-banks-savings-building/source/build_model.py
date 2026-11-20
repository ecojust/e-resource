"""Package the original local bank exterior at 261 Sichuan Middle Road."""
from pathlib import Path
import sys
import os
import argparse
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from four_banks_geometry import PALETTE,add_building

ID='huangpu-four-banks-savings-building'
SCOPE='四川中路261号、汉口路西北街角，依据2014年街照、2019年航拍及2024年修缮介绍复原两层白石柱座、四层棕砖、浅色上层、斜切拱门和八角塔冠。屋顶背部、标高和两面共墙按资料估计。'
META={'id':ID,'name':'四行储蓄会大楼（四川中路261号联合大楼）','status':'original-photo-informed-exterior','viewer_page':'four-banks-savings-building.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Metres. Local +X lies 13.35 degrees north of true east, local +Y follows Sichuan Middle Road northward. The clipped main entrance faces southeast. Map heading −13.35 degrees.','copyright':'Original geometry MIT. No photographs or prior models embedded.'}
if __name__=='__main__':
    # Preserve the packager's --blender option and its argv, including a
    # system-specific launcher, while setting our local camera before save.
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['FOUR_BANKS_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
