"""Build the six-storey former Yokohama Specie Bank at 24 Zhongshan East 1st Road."""
from pathlib import Path
import sys
import os
import argparse
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from yokohama_geometry import PALETTE,add_building

ID='huangpu-yokohama-specie-bank'
SCOPE='中山东一路24号横滨正金银行的现状外观。东立面三道铜门、二至五层双爱奥尼克巨柱、两侧悬挑阳台、工商银行标识与退后六层按现状照片建模。完整L形建筑轮廓据具名底图，西后翼屋盖依据航片估计。'
META={'id':ID,'name':'横滨正金银行大楼（外滩24号）','status':'original-photo-informed-exterior','viewer_page':'yokohama-specie-bank.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Metres. +X faces the river 8.5824 degrees south of east. The map heading is +8.5824 degrees.','copyright':'Original geometry MIT. No images or historical meshes embedded.'}
if __name__=='__main__':
    # Preserve the packager's --blender option and its argv, including a
    # system-specific launcher, while setting our local camera before save.
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['YOKOHAMA_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
