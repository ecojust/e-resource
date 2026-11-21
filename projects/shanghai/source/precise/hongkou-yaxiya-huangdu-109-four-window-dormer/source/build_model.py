"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from huangdu_dormer import PALETTE,model
META={'id': 'hongkou-yaxiya-huangdu-109-four-window-dormer', 'name': '亚细亚里黄渡路109号四窗老虎窗与瓦坡', 'viewer_page': 'yaxiya-huangdu-109-four-window-dormer.html', 'scope': '取黄渡路109号2014年街照中并列四窗的横向老虎窗，含前脸、挑檐、浅坡红瓦与左侧相接的陡瓦面。', 'model_scope_zh': '取黄渡路109号2014年街照中并列四窗的横向老虎窗，含前脸、挑檐、浅坡红瓦与左侧相接的陡瓦面。', 'status': 'independent-historic-fragment', 'interiors_modeled': False, 'coordinate_convention': 'Local metres. X follows the window row to the right, Y rises back into the roof and Z is vertical.', 'source_register': 'source/precise/hongkou-yaxiya-huangdu-109-four-window-dormer/reference-review.json', 'estimated': 'Relative facade spacing and roof profiles follow the 2014 oblique photograph. Absolute dimensions, tile laps and hidden depths are estimated.'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['HUANGDU_DORMER_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
