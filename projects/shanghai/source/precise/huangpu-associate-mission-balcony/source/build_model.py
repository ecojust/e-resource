"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-associate-mission-balcony', 'name': '协进大楼沿街五格透花石阳台与挑托', 'viewer_page': 'associate-mission-central-balcony.html', 'scope': '沿街深色砖墙中段的一座石阳台，含前脸五格放射形透栏、方形端柱、转角短栏、叠级底板和两只弧形挑托。', 'model_scope_zh': '沿街深色砖墙中段的一座石阳台，含前脸五格放射形透栏、方形端柱、转角短栏、叠级底板和两只弧形挑托。', 'interiors_modeled': False, 'status': 'photographed-street-elevation-fragment', 'coordinate_convention': 'X follows the photographed facade, Y increases backwards, Z is up.', 'source_register': 'source/precise/huangpu-associate-mission-balcony/reference-review.json', 'estimated': '以栏柱估算栏板通高约0.8米。浮雕倒角、托臂下部弧度与阳台背面按正斜两侧的透视比例近似。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['ASSOCIATE_BALCONY_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
