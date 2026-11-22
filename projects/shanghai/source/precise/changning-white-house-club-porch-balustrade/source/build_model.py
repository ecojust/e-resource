"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'changning-white-house-club-porch-balustrade', 'name': '白宫俱乐部廊顶瓶栏与浮雕柱头', 'viewer_page': 'white-house-club-porch-balustrade.html', 'scope': '1390号小白楼正面门廊的两根圆柱、浮雕柱头、齿形檐带和三面瓶栏，连同廊后的半圆券。', 'model_scope_zh': '1390号小白楼正面门廊的两根圆柱、浮雕柱头、齿形檐带和三面瓶栏，连同廊后的半圆券。', 'interiors_modeled': False, 'status': 'photograph-based-architectural-detail', 'coordinate_convention': 'X follows the principal visible elevation, Y recedes into the roof and Z points up.', 'source_register': 'source/precise/changning-white-house-club-porch-balustrade/reference-review.json', 'estimated': '图片中正面辨出十二支瓶柱。两侧回栏的深度、浮雕轮廓、背面和绝对尺寸按正斜照片近似。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['WHITE_HOUSE_BALCONY_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
