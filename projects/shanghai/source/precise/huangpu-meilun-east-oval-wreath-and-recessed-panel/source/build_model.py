"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-meilun-east-oval-wreath-and-recessed-panel', 'name': '美伦大楼东楼椭圆花环与层叠窗裙', 'viewer_page': 'meilun-east-oval-wreath-and-recessed-panel.html', 'scope': '取2018年东楼具名照中靠街角的两扇方窗、其间带椭圆花环的窄壁柱和窗下三重长方框饰。', 'model_scope_zh': '取2018年东楼具名照中靠街角的两扇方窗、其间带椭圆花环的窄壁柱和窗下三重长方框饰。', 'interiors_modeled': False, 'status': 'photographed-street-elevation-fragment', 'coordinate_convention': 'X follows the photographed facade, Y increases backwards, Z is up.', 'source_register': 'source/precise/huangpu-meilun-east-oval-wreath-and-recessed-panel/reference-review.json', 'estimated': '以右窗净宽约1.70米为比例。花叶数量、背面和窗内侧按影像估计；本件是朝街窗间墙局部。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['MEILUN_EAST_WREATH_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
