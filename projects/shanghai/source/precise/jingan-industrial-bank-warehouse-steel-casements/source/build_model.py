"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'jingan-industrial-bank-warehouse-steel-casements', 'name': '中国实业银行仓库南面高段双层钢窗与折纹窗楣', 'viewer_page': 'industrial-bank-warehouse-steel-casements.html', 'scope': '北苏州路1028号南立面中央高段的上下两排钢窗、实照所见外开窗扇、窗间三块矩形饰板及分列的浅浮雕。', 'model_scope_zh': '北苏州路1028号南立面中央高段的上下两排钢窗、实照所见外开窗扇、窗间三块矩形饰板及分列的浅浮雕。', 'interiors_modeled': False, 'status': 'independent-photograph-based-facade-detail', 'coordinate_convention': 'X follows the river elevation, Y recedes into the front wall, Z is up.', 'source_register': 'source/precise/jingan-industrial-bank-warehouse-steel-casements/reference-review.json', 'estimated': '所绘为发布图中可辨的修缮现状。洞宽暂取4.40米以定比例，型钢截面、开扇角度、窗楣凿刻深度与背面按照片推定。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['WAREHOUSE_CASEMENT_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
