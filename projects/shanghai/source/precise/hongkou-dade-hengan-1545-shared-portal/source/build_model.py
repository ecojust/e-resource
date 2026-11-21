"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from dade_portal import PALETTE,model
META={'id': 'hongkou-dade-hengan-1545-shared-portal', 'name': '大德里与恒安坊四川北路1545弄题名过街门', 'viewer_page': 'dade-hengan-1545-shared-portal.html', 'scope': '四川北路1545弄临街的单处共享过街门，含双题名石额、两侧1545弄绿牌、阶状曲托、石门垛及左侧铁栅。', 'model_scope_zh': '四川北路1545弄临街的单处共享过街门，含双题名石额、两侧1545弄绿牌、阶状曲托、石门垛及左侧铁栅。', 'interiors_modeled': False, 'status': 'independent-historic-fragment', 'coordinate_convention': 'Metres. X to the right facing the lane, Y into the passage and Z above the street threshold.', 'source_register': 'source/precise/hongkou-dade-hengan-1545-shared-portal/reference-review.json', 'estimated': 'Absolute dimensions estimated from photographed proportions.'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['DADE_GATE_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
