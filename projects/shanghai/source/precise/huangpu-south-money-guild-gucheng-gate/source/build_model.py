"""Build the south brick gateway of the rebuilt Shanghai South Money Guild."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from park_gate import PALETTE, gate

MODEL_ID = 'huangpu-south-money-guild-gucheng-gate'
SCOPE = ('古城公园迁建现址的南面砖雕门楼，以2014年门额细照、2015年地面及西侧高处照片和2020年南侧航照为据。'
         '模型包括三道石券和黑色双扇门、三块起翘瓦檐、六字凸刻门额、石阶与门枕。')
META = {
    'id':MODEL_ID,'name':'沪南钱业公所古城公园南面三券砖雕门楼',
    'status':'original-photo-informed-exterior','viewer_page':'south-money-guild-gucheng-gate.html',
    'scope':SCOPE,'model_scope_zh':SCOPE,'interiors_modeled':False,
    'source_register':f'source/precise/{MODEL_ID}/reference-review.json',
    'estimated':'门面宽约19.4米，三个门轴相距约4米。高度取自27毫米等效视角的照片拟合。瓦片断面、浅浮雕轮廓、侧端遮挡部分按同段影像估计。',
    'coordinate_convention':'Local X runs east along the south gateway, Y north into the park building and Z up.',
    'copyright':'Original geometry and materials, MIT. Inscription font subset under SIL OFL 1.1. Photographs are credited as independent study sources.',
}

if __name__=='__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['GUILD_GATE_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, gate)
