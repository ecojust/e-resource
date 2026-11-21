"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from paired_windows import PALETTE,model
META={'id': 'changning-shengshi-garden-paired-windows', 'name': '盛世花园临街双联钢窗与铁花架', 'viewer_page': 'shengshi-garden-paired-windows.html', 'scope': '武定西路交会处上部外墙的一段，有上下两对钢窗、深色活动百叶、双格外挑铁花架与檐口。', 'model_scope_zh': '盛世花园临街双联钢窗与铁花架', 'interiors_modeled': False, 'status': 'photograph-based-architectural-detail', 'coordinate_convention': 'X runs along the window wall, Y towards the room, Z upright.', 'source_register': 'source/precise/changning-shengshi-garden-paired-windows/reference-review.json', 'estimated': '以窗洞约1.02米宽为比例尺。标高、挑距、石材、百叶片数和小铁圈间隔为照片估计。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['SHENGSHI_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
