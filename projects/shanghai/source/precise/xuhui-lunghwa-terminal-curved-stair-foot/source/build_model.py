"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from stair_foot import PALETTE,add_stair
META={'id': 'xuhui-lunghwa-terminal-curved-stair-foot', 'name': '龙华机场旧候机厅弧形楼梯下段', 'viewer_page': 'lunghwa-terminal-curved-stair.html', 'scope': '下六级室内石阶、双侧外撇石挡墙、黄铜扶手和方端柱。', 'model_scope_zh': '下六级室内石阶、双侧外撇石挡墙、黄铜扶手和方端柱。', 'interiors_modeled': True, 'status': 'independent-historic-fragment', 'coordinate_convention': 'X toward the right-hand newel, Y upstairs, Z above the bottom floor.', 'source_register': 'source/precise/xuhui-lunghwa-terminal-curved-stair-foot/reference-review.json', 'estimated': '一级高0.154米、踏步深0.305米为近似比例基准。总宽、柱高及扶手弧线按图配合，未经现场测量。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['LUNGHWA_WINDOW_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_stair)
