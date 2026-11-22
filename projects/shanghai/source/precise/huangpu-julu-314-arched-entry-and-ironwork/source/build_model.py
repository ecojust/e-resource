"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-julu-314-arched-entry-and-ironwork', 'name': '巨鹿路314号住宅弧券门架与铁花双扇', 'viewer_page': 'julu-314-arched-entry-and-ironwork.html', 'scope': '取临街白灰弧券、两侧方墩、叠线墩帽和两扇院门的黑铁花。照片中红色衬板和现状样式标为拍摄时的外观。', 'model_scope_zh': '取临街白灰弧券、两侧方墩、叠线墩帽和两扇院门的黑铁花。照片中红色衬板和现状样式标为拍摄时的外观。', 'interiors_modeled': False, 'status': 'photographed-street-elevation-fragment', 'coordinate_convention': 'X follows the photographed facade, Y increases backwards, Z is up.', 'source_register': 'source/precise/huangpu-julu-314-arched-entry-and-ironwork/reference-review.json', 'estimated': '按双扇院门净宽约2.45米推算。墩柱后侧、券体进深和门板厚度依据正照、斜照估算。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['JULU314_GARDEN_GATE_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
