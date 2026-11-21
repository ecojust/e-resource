"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from garden_balcony import PALETTE,add_balcony
META={'id': 'xuhui-yongjia-630-arched-balcony', 'name': '永嘉路630号花园住宅二层拱窗与菱格阳台', 'viewer_page': 'yongjia-630-arched-balcony.html', 'scope': '二层券形阳台上的通长线脚、盾形装饰、双柱、象牙白六扇窗、相交圆环与菱格栏板。', 'model_scope_zh': '1925年住宅的上层阳台构件，以2013年正面和侧面近照为依据。', 'interiors_modeled': False, 'status': 'standalone-historic-balcony', 'coordinate_convention': 'Metres. X points right in the 2013 near-frontal photograph; positive Y recedes from the balcony face. Height origin is near the underside of the consoles.', 'source_register': 'source/precise/xuhui-yongjia-630-arched-balcony/reference-review.json', 'estimated': '栏杆、柱距、券径和玻璃分格之间的比例来自2013年照片。绝对尺度以门窗常见尺度估计，券罩和阳台进深依据侧向照片。', 'copyright': 'Original geometric reconstruction. Third-party historical photographs and printed material are cited in the source register.'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['YONGJIA_BALCONY_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_balcony)
