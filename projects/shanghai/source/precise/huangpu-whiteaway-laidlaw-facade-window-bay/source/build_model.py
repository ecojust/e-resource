"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-whiteaway-laidlaw-facade-window-bay', 'name': '惠罗公司大楼沿街竖带与横梃格窗', 'viewer_page': 'whiteaway-laidlaw-facade-window-bay.html', 'scope': '取营业层以上一开间的浅色双边竖向壁带、两层成对的矩形深窗、横窗梃及窗间墙。', 'model_scope_zh': '取营业层以上一开间的浅色双边竖向壁带、两层成对的矩形深窗、横窗梃及窗间墙。', 'interiors_modeled': False, 'status': 'photographed-street-elevation-fragment', 'coordinate_convention': 'X follows the photographed facade, Y increases backwards, Z is up.', 'source_register': 'source/precise/huangpu-whiteaway-laidlaw-facade-window-bay/reference-review.json', 'estimated': '以一层窗宽约1.4米估算。立面净高、壁带前突、深色内框与玻璃后的形态为相对尺度近似；店招与现代广告未建模。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['WHITEAWAY_WINDOW_BAY_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
