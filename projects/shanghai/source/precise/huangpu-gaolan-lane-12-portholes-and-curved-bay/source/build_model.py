"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-gaolan-lane-12-portholes-and-curved-bay', 'name': '皋兰路12弄街面住宅双层圆窗与弧形带窗', 'viewer_page': 'gaolan-lane-12-portholes-and-curved-bay.html', 'scope': '市表第五批第15行写皋兰路12号；照片中的市级铭牌实写皋兰路12弄1–4号，皋兰路10号、14号。建模取铭牌后方的两层街面弧窗、同层圆窗和夹在窗带之间的水刷石带。', 'model_scope_zh': '市表第五批第15行写皋兰路12号；照片中的市级铭牌实写皋兰路12弄1–4号，皋兰路10号、14号。建模取铭牌后方的两层街面弧窗、同层圆窗和夹在窗带之间的水刷石带。', 'interiors_modeled': False, 'status': 'independent-photograph-based-facade-detail', 'coordinate_convention': 'Horizontal X spans the two window groups. Negative Y points out from the street elevation. Z is up.', 'source_register': 'source/precise/huangpu-gaolan-lane-12-portholes-and-curved-bay/reference-review.json', 'estimated': '圆窗净径暂取1.02米。曲面半径与转角、窗后深度、外墙厚度及遮蔽部分按照片比例估计。下层明色窗框及上层深色钢窗按2018年拍摄状态表达。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['GAOLAN_PORT_WINDOW_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
