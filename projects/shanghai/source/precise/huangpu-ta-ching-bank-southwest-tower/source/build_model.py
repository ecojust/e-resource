"""Rebuild the documented southwest corner tower of the Ta-Ching Government Bank."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from tower_front import PALETTE,add_building

ID='huangpu-ta-ching-bank-southwest-tower'
META={'id': 'huangpu-ta-ching-bank-southwest-tower', 'name': '大清银行上海分行旧址（西南八角塔楼）', 'viewer_page': 'ta-ching-bank-southwest-tower.html', 'scope': '四川中路与汉口路西南转角临街的三面塔身、相邻短窗墙、低鼓座与矮铜穹。', 'model_scope_zh': '依2017年修缮后署日照片及2021年刊载的近照制作。南主入口上方的高穹顶与整段街墙另列。', 'status': 'original-photo-informed-exterior', 'reference_height_m': 19.35, 'estimated': '以5.324米的冻结地块切角校准。窗宽、楼层高度、塔冠曲线与接墙厚度按照片比例估算。', 'coordinate_convention': 'Right-handed local metres. +X along the chamfer to the southeast, +Y northeast into the building, +Z up.', 'source_register': 'source/precise/huangpu-ta-ching-bank-southwest-tower/reference-review.json', 'interiors_modeled': False, 'copyright': 'Original geometry and authored red brick pattern; photographs used for study only.'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,remainder=parser.parse_known_args()
    os.environ['TACHING_BLENDER']=options.blender
    sys.argv[1:]=[*remainder,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
