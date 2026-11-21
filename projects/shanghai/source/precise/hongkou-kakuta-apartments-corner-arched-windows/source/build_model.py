"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from corner_windows import PALETTE,model
META={'id': 'hongkou-kakuta-apartments-corner-arched-windows', 'name': '角田公寓转角两组双联拱窗', 'viewer_page': 'kakuta-apartments-corner-arched-windows.html', 'scope': '原五层沿街转角相邻两个折面上的四扇圆头窗，含弧顶气窗、双扇竖框、转角凸带、石窗台及2024年可辨的分片窗罩。', 'model_scope_zh': '原五层沿街转角相邻两个折面上的四扇圆头窗，含弧顶气窗、双扇竖框、转角凸带、石窗台及2024年可辨的分片窗罩。', 'interiors_modeled': False, 'status': 'independent-historic-fragment', 'coordinate_convention': 'Metres. Origin at the shared street arris at the base of the modelled wall strip. X to photographic right, Y indoors and Z upwards.', 'source_register': 'source/precise/hongkou-kakuta-apartments-corner-arched-windows/reference-review.json', 'estimated': '窗净宽及窗台深度为建模估值；角度由西楼OSM连续边回算，不是对窗下街墙的测绘。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['KAKUTA_WINDOW_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
