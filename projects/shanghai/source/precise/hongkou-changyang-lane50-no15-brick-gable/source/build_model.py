"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from brick_gable import PALETTE,model
META={'id': 'hongkou-changyang-lane50-no15-brick-gable', 'name': '长阳路50弄15号圆饰山墙与双层砖券门面', 'viewer_page': 'changyang-lane50-no15-brick-gable.html', 'scope': '按2015年2月3日实照复原弄内15号门牌所在的一开间，包含花形砖圆饰、逐级叠出的山墙檐、二层弧顶窗、一层砖券、绿色号牌及三阶石级。', 'model_scope_zh': '按2015年2月3日实照复原弄内15号门牌所在的一开间，包含花形砖圆饰、逐级叠出的山墙檐、二层弧顶窗、一层砖券、绿色号牌及三阶石级。', 'status': 'historical-photograph-reconstruction', 'interiors_modeled': False, 'coordinate_convention': 'X follows the facade. Positive Y runs back into the building. Z is above the garden path.', 'source_register': 'source/precise/hongkou-changyang-lane50-no15-brick-gable/reference-review.json', 'estimated': 'Proportions follow the 2015 photograph. Absolute scale, masonry depth, arch thickness and the shape of the obscured inner door are estimates.'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['CHANGYANG_GABLE_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
