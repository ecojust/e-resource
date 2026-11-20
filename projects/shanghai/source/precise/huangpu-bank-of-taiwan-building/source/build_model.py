"""Build the two photographed street fronts of the former Bank of Taiwan."""
from pathlib import Path
import argparse
import os
import sys
SRC=Path(__file__).resolve().parent
sys.path.insert(0,str(SRC.parents[3]/'tools'))
from package_architectural_model import build
from bank import PALETTE,bank
ID='huangpu-bank-of-taiwan-building'
SCOPE='外滩16号台湾银行大楼2014年临中山东一路的四柱门厅及九江路七开间高街墙。西端低翼、屋顶设备、北侧字林大楼及街南15号另列。'
META={'id':ID,'name':'台湾银行大楼东门厅与九江路街面','status':'original-photo-informed-exterior','viewer_page':'bank-of-taiwan.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':'东面宽约18.11米；七开间侧墙约40米，檐高、柱径、石饰和开口使用照片约估。','interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json','coordinate_convention':'Local +X approximately north along the Bund, +Y west into the property, +Z up.','copyright':'Original geometry and materials, MIT. Sign glyphs derived from Noto Serif CJK SC under SIL OFL 1.1. Photos are not embedded.'}
if __name__=='__main__':
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['TAIWAN_BANK_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SRC/'blender_preview.py')]
    build(SRC,META,PALETTE,bank)
