"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-shanghai-bank-beijing-205-grille', 'name': '上海银行旧楼北京东路205号几何铁格门与上亮窗', 'viewer_page': 'shanghai-bank-beijing-205-grille.html', 'scope': '以带205号门牌的具名照片为据，取里侧成排方折铁格、框上竖向钢条、门头棕色横枋、上亮窗和两侧浅灰色勒脚。', 'model_scope_zh': '以带205号门牌的具名照片为据，取里侧成排方折铁格、框上竖向钢条、门头棕色横枋、上亮窗和两侧浅灰色勒脚。', 'interiors_modeled': False, 'status': 'photographed-street-elevation-fragment', 'coordinate_convention': 'X follows the photographed facade, Y increases backwards, Z is up.', 'source_register': 'source/precise/huangpu-shanghai-bank-beijing-205-grille/reference-review.json', 'estimated': '以绿色铁门净宽约1.43米、净高约2.38米为约束。门后院落及室内不可见，窗棂和方折铁条的截面按相片估计。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['SHANGHAI_BANK_205_GRILLE_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
