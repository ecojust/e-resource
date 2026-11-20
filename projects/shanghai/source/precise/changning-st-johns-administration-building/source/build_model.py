"""Build the south veranda, iron carriage porch and lookout of the former Hogg’s House."""
from pathlib import Path
import argparse
import os
import sys
SRC=Path(__file__).resolve().parent
sys.path.insert(0,str(SRC.parents[3]/'tools'))
from package_architectural_model import build
from hogg_house import PALETTE,building
ID='changning-st-johns-administration-building'
SCOPE='霍格别墅改用的四号楼，按华东政法大学校史照片制作南廊、镂空栏板、乘车门廊与屋顶望楼。北部房间、未核侧墙和其他校园楼宇另列。'
META={'id':ID,'name':'圣约翰大学校政厅（四号楼）南廊与望楼','status':'original-photo-informed-exterior','viewer_page':'st-johns-administration.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':'南廊进深3米取自校方档案。宽约26.6米，望楼和曲线铁皮檐高度、退距按照片估计。','interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json','coordinate_convention':'Local +X east along the southern front. Positive Y is inward to the north, positive Z is up.','copyright':'Original geometry and materials, MIT. Photographs are external references.'}
if __name__=='__main__':
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['HOGG_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SRC/'blender_preview.py')]
    build(SRC,META,PALETTE,building)
