"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from stair_windows import PALETTE,add_stair_windows
META={'id': 'xuhui-georgia-apartments-stair-window-fins', 'name': '会斯乐公寓衡山路楼梯间竖窗与水泥线板', 'viewer_page': 'georgia-apartments-stair-window-fins.html', 'scope': '面向衡山路的中央楼梯间西南一对竖窗、围框、水泥竖线和两层窗间墙。', 'model_scope_zh': '中央楼梯间西南一对竖窗的连续两层与三道竖向水泥线板。', 'interiors_modeled': False, 'status': 'photo-measured-stair-windows', 'coordinate_convention': '+X southwest along the northwest facade, +Y towards the interior, local Z above base of selected two-level fragment.', 'source_register': 'source/precise/xuhui-georgia-apartments-stair-window-fins/reference-review.json', 'estimated': '照片能实辨四扇窗、两列八格钢窗和三条水泥线板。绝对窗宽、楼层标高和线板出挑由透视与总楼高估计。', 'copyright': 'Original architectural meshes. Photographs and original drawings are credited separately.'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['GEORGIA_APARTMENTS_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_stair_windows)
