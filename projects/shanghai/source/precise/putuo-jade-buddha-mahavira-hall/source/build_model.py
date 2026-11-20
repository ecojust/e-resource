"""Build the relocated Mahavira Hall of Shanghai Jade Buddha Temple."""
from pathlib import Path
import sys
import os
import argparse
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from hall_geometry import PALETTE,add_building
ID='putuo-jade-buddha-mahavira-hall'
SCOPE='安远路170号2017年平移后的大雄宝殿。寺方实照与寺院图证实灰瓦重檐歇山、上翘檐角、四方金字匾、黄色山墙、花格木门和前台阶。高宽、台基、受遮挡的侧背与细部为照片比例估计。前庭和侧殿单独保留。'
META={'id':ID,'name':'玉佛禅寺大雄宝殿','status':'original-photo-informed-exterior','viewer_page':'jade-buddha-mahavira-hall.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Metres, Z up. +X follows the ridge northeast, +Y points northwest toward the rear and the photographed entrance faces -Y.','copyright':'Original exterior geometry under MIT. Photographs used for reference only.'}
if __name__=='__main__':
    # Preserve the packager's --blender option and its argv, including a
    # system-specific launcher, while setting our local camera before save.
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['JADE_HALL_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
