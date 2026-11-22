"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-metropole-east-wing-brick-window-pair', 'name': '都城饭店东楼福州路双色墙角与双券窗', 'viewer_page': 'metropole-east-wing-brick-window-pair.html', 'scope': '福州路106号红砖临街面的一段，包括进退交替的白色转角石、相邻两扇浅弧券窗、窗前细横杆与上下两条水平檐线。', 'model_scope_zh': '福州路106号红砖临街面的一段，包括进退交替的白色转角石、相邻两扇浅弧券窗、窗前细横杆与上下两条水平檐线。', 'interiors_modeled': False, 'status': 'photographed-Fuzhou-Road-street-elevation-fragment', 'coordinate_convention': 'X runs along the street from the pale corner, Y towards the room, Z upwards.', 'source_register': 'source/precise/huangpu-metropole-east-wing-brick-window-pair/reference-review.json', 'estimated': '以两扇窗净宽约1.12米为图像比例基准。券面和墙垛进深、窗扇内侧构造及墙面片段高度是外观估计。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['METROPOLE_EAST_BRICK_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
