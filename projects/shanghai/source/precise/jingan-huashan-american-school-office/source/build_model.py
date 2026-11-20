"""Build the historic school office at 639/643 Huashan Road from its source geometry."""
from pathlib import Path
import sys
import os
import argparse
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from huashan_office_geometry import PALETTE,add_building
ID='jingan-huashan-american-school-office'
SCOPE='华山路639、643号院内原美国学校红瓦办公楼的临街面与临草坪面。639号历史照片证实拱形门斗，2024年实景证实双层方柱廊、曲线铁栏及转角露台。屋面、端部和隐蔽处按比例估算。马兰花剧场及其余附楼另计。'
META={'id':ID,'name':'华山路原美国学校办公楼','status':'original-photo-informed-exterior','viewer_page':'huashan-school-office.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Metres, Z up. +X runs southwest along Huashan Road and +Y faces southeast onto the lawn. The street portal projects toward -Y.','copyright':'Original exterior geometry under MIT. Photographs used for reference only.'}
if __name__=='__main__':
    # Preserve the packager's --blender option and its argv, including a
    # system-specific launcher, while setting our local camera before save.
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['HUASHAN_OFFICE_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
