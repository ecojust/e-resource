"""Build the 1922 classroom range at 10 Hengshan Road from its source geometry."""
from pathlib import Path
import sys
import os
import argparse
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from american_school_geometry import PALETTE,add_building
ID='xuhui-shanghai-american-school-main'
SCOPE='衡山路10号1922年美童公学主教学楼的东侧长翼。参考2011、2013及2017年的正面照片、徐汇区文化局档案和校史影像，重建两层红砖窗墙、中央石门楣、老虎窗与白色尖顶钟亭。屋高、屋顶背面、后窗与隐蔽处按比例估计。'
META={'id':ID,'name':'美童公学主楼（衡山路10号）','status':'original-photo-informed-exterior','viewer_page':'american-school-hengshan.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Metres, Z up. +X runs northeast along the 75.50 m southeast facade. +Y leads northwest toward the retained campus wing. Map heading is minus 56.82171685034 degrees.','copyright':'Original exterior geometry under MIT. Photographs used for reference only.'}
if __name__=='__main__':
    # Preserve the packager's --blender option and its argv, including a
    # system-specific launcher, while setting our local camera before save.
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['AMERICAN_SCHOOL_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
