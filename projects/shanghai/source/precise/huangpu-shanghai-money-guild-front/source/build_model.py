"""Rebuild the documented Ningbo Road facade of the Shanghai Money Guild."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from guild_front import PALETTE,add_building

ID='huangpu-shanghai-money-guild-front'
META={'id': 'huangpu-shanghai-money-guild-front', 'name': '上海钱业公会大楼（宁波路三开间正面）', 'viewer_page': 'shanghai-money-guild-front.html', 'scope': '按宁波路276号三开间正面照片制作中央券门和双侧门柱、三组长窗、三座铁栏挑阳台、托底牛腿、穗饰及上檐。', 'reference_height_m': 15.7, 'status': 'original-photo-informed-exterior', 'estimated': '街面宽度据冻结足印边测算，窗深、浮雕及铁栏截面按照片估算。', 'coordinate_convention': 'Right-handed Z up; local X east-northeast along Ningbo Road, local +Y into the building. Metres.', 'source_register': 'source/precise/huangpu-shanghai-money-guild-front/reference-review.json', 'interiors_modeled': False, 'copyright': 'Original geometry and authored buff masonry grain. Photographs used for reference only.', 'model_scope_zh': '按宁波路276号三开间正面照片制作中央券门和双侧门柱、三组长窗、三座铁栏挑阳台、托底牛腿、穗饰及上檐。'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,remainder=parser.parse_known_args()
    os.environ['MONEY_GUILD_BLENDER']=options.blender
    sys.argv[1:]=[*remainder,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
