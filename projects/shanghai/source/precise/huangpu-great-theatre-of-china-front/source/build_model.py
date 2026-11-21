"""Rebuild the documented twin-tower Chinese opera house entrance in Niuzhuang Road."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from entrance import PALETTE,add_building

ID='huangpu-great-theatre-of-china-front'
META={'id': 'huangpu-great-theatre-of-china-front', 'name': '中国大戏院牛庄路双塔入口', 'viewer_page': 'great-theatre-of-china-front.html', 'scope': '中央两根砖塔、两组各三窗和中英文题名的挑篷、内退门扇。', 'model_scope_zh': '牛庄路704号正入口。2018年修复的锥尖和当前外墙分期记录。', 'status': 'original-photo-informed-exterior', 'reference_height_m': 23.2, 'estimated': '上海发布建筑可阅读给整宅23.2米；此断面锥尖据该高度校定，分层非量测。', 'coordinate_convention': 'Local metres, +X along the Niuzhuang Road facade, +Y inward, +Z up.', 'source_register': 'source/precise/huangpu-great-theatre-of-china-front/reference-review.json', 'interiors_modeled': False, 'copyright': 'Original artwork, geometry and synthesized masonry appearance. Font-derived signs are typographic reconstructions.'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,remainder=parser.parse_known_args()
    os.environ['CHINA_THEATRE_BLENDER']=options.blender
    sys.argv[1:]=[*remainder,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
