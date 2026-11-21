"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from portal import PALETTE,model
META={'id': 'yangpu-hujiang-haskell-gymnasium-arched-portal', 'name': '沪江大学北体育馆历史入口石券', 'viewer_page': 'hujiang-haskell-gymnasium-arched-portal.html', 'scope': '历史正门的浅尖券、三道突出线脚、券下竖梃上亮、内退双扇和门槛。', 'model_scope_zh': '沪江大学北体育馆主入口石券', 'interiors_modeled': False, 'status': 'historical-photograph-reconstruction', 'coordinate_convention': 'X follows the entrance front, Y runs into the doorway, Z is vertical.', 'source_register': 'source/precise/yangpu-hujiang-haskell-gymnasium-arched-portal/reference-review.json', 'estimated': '两扇门净宽假设约1.75米，线脚退距、门框厚度与石面颜色为估计。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['HASKELL_PORTAL_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
