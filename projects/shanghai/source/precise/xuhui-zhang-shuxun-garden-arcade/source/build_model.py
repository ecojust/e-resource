"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from garden_arcade import PALETTE,add_arcade
META={'id': 'xuhui-zhang-shuxun-garden-arcade', 'name': '张叔驯故居花园面三联钢窗券廊', 'viewer_page': 'zhang-shuxun-garden-arcade.html', 'scope': '历史住宅花园面底层三个半圆券、钢窗和两根雕花柱。', 'model_scope_zh': '三联半圆券窗，含两柱叶饰柱头、双弧扇光、二十格钢窗和红色门槛。', 'interiors_modeled': False, 'status': 'independent-historic-fragment', 'coordinate_convention': 'X right on the garden photograph; Y recedes into wall; Z above threshold.', 'source_register': 'source/precise/xuhui-zhang-shuxun-garden-arcade/reference-review.json', 'estimated': '无公开现场实测尺。采用中央净宽1.56 m作为建模基准，柱／窗尺寸随其同比变化。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['TIANPING_WINDOW_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_arcade)
