"""Package the original local bank exterior at 89 Jiujiang Road."""
from pathlib import Path
import sys
import os
import argparse
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from jiangchuan_geometry import PALETTE,add_building

ID='huangpu-deutsch-asiatische-bank'
SCOPE='九江路89号、四川中路294号。以政府现场铭牌、街角现照和历史图重建窗后退的两街科林斯通柱、巴洛克门楣及1988年加高两层。层高、侧后与屋顶按外部资料估计。'
META={'id':ID,'name':'江川大楼（德华银行九江路营业楼）','status':'original-photo-informed-exterior','viewer_page':'deutsch-asiatische-bank.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Metres. +X is 16.55 degrees north of east. The chamfered main portal faces the northwest junction. Map heading −16.55 degrees.','copyright':'Original geometry MIT. No images or historical meshes embedded.'}
if __name__=='__main__':
    # Preserve the packager's --blender option and its argv, including a
    # system-specific launcher, while setting our local camera before save.
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['JIANGCHUAN_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
