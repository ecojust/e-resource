"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'changning-yuyuan-new-village-swept-gable', 'name': '愚园新村排屋灰砖山墙与弯折封檐', 'viewer_page': 'yuyuan-new-village-swept-gable.html', 'scope': '规资局原图靠近镜头的灰砖端山墙。模型取屋檐折线、两层窄窗、红砖水平带与一段退后的坡瓦面。', 'model_scope_zh': '端山墙、窗洞与灰白封檐', 'interiors_modeled': False, 'status': 'photograph-based-architectural-detail', 'coordinate_convention': 'X along gable; Y behind the brick face; Z upright. Side and rear cut above the undocumented lower floor.', 'source_register': 'source/precise/changning-yuyuan-new-village-swept-gable/reference-review.json', 'estimated': '两道砖带与屋脊高度按原照相对量测。取端墙净宽6.40米作展示比例，屋前草地及室内没有实测定尺。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['YUYUAN_GABLE_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
