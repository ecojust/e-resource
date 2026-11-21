"""Rebuild the photograph-bound central portal and carved stone hood."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from portal import PALETTE,add_building

ID='huangpu-salt-industry-bank-entrance'
META={'id': 'huangpu-salt-industry-bank-entrance', 'name': '盐业大楼北京东路280号门罩与石栏', 'viewer_page': 'salt-industry-bank-entrance.html', 'scope': '民国银行南面前伸门罩与石栏，含中部圆牌、两端方壁柱、内侧一对塔司干圆柱和浅退入拱头。', 'reference_height_m': 6.87, 'status': 'original-photo-informed-exterior', 'estimated': '照片估算宽约8.2米，弧栏与柱头厚度、门扇退距由多期照片对照。', 'coordinate_convention': 'Right-handed Z up, local X east approximately along Beijing Road, local Y into the building. Metres.', 'source_register': 'source/precise/huangpu-salt-industry-bank-entrance/reference-review.json', 'interiors_modeled': False, 'copyright': 'Original geometric reconstruction and original procedural granite grain; referenced photographs are not embedded.', 'model_scope_zh': '民国银行南面前伸门罩与石栏，含中部圆牌、两端方壁柱、内侧一对塔司干圆柱和浅退入拱头。'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,remainder=parser.parse_known_args()
    os.environ['SALT_PORTICO_BLENDER']=options.blender
    sys.argv[1:]=[*remainder,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
