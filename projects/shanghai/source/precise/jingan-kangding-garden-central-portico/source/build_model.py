"""Rebuild the three-bay south-facing loggia at Kangding Garden."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from kangding_loggia import PALETTE,add_building

META={'id': 'jingan-kangding-garden-central-portico', 'name': '康定花园中楼南向三开间柱廊', 'viewer_page': 'kangding-central-portico.html', 'status': 'photo-informed-garden-loggia', 'scope': '依据上海静安编《静安文博钩沉》发表外景及2022年一颗螺丝东正面图，复建中楼南面三开间凹廊、双通高圆柱、两端壁柱、三道微弧通透石栏、实心回纹栏墙与中央老虎窗。东西两栋、两侧凸间、连桥及庭院余景保留。', 'reference_height_m': 16.6, 'estimated': '中楼南边线28.90米来自名录足印。中央段模型宽16.84米、高16.60米，栏深、柱径与檐部尺寸按照片估算。', 'coordinate_convention': 'Local metres. X follows the garden-facing central elevation to the right, Y points into the middle house, Z is up.', 'source_register': 'source/precise/jingan-kangding-garden-central-portico/reference-review.json', 'interiors_modeled': False, 'copyright': 'Original geometry and generated ceramic roof tile pattern, MIT. Photographs are cited as measurement references only.', 'model_scope_zh': '依据上海静安编《静安文博钩沉》发表外景及2022年一颗螺丝东正面图，复建中楼南面三开间凹廊、双通高圆柱、两端壁柱、三道微弧通透石栏、实心回纹栏墙与中央老虎窗。东西两栋、两侧凸间、连桥及庭院余景保留。'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,remainder=parser.parse_known_args()
    os.environ['KANGDING313_BLENDER']=options.blender
    sys.argv[1:]=[*remainder,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
