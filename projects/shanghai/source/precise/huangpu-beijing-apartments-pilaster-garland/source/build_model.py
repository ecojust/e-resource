"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-beijing-apartments-pilaster-garland', 'name': '北京公寓街面椭圆花饰壁柱与双层窗楣', 'viewer_page': 'beijing-apartments-pilaster-garland.html', 'scope': '取北京东路163号红砖立面上一跨较高窗列和相邻通高壁柱，包含上层的浅砖券、白色券心、铁栏，下层的三角窗楣、长梯形垂石，以及壁柱上的椭圆花环。', 'model_scope_zh': '取北京东路163号红砖立面上一跨较高窗列和相邻通高壁柱，包含上层的浅砖券、白色券心、铁栏，下层的三角窗楣、长梯形垂石，以及壁柱上的椭圆花环。', 'interiors_modeled': False, 'status': 'independent-photograph-based-facade-detail', 'coordinate_convention': 'X follows the photographed street elevation, Y recedes into the front wall, Z is up.', 'source_register': 'source/precise/huangpu-beijing-apartments-pilaster-garland/reference-review.json', 'estimated': '上窗净宽暂取1.55米。出檐、窗后深度、铁花曲线和砖块尺寸按斜照片比例估计。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['BEIJING_PILASTER_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
