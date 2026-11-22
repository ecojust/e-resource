"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from arcade import PALETTE,model
META={'id': 'changning-chartered-bank-garden-twin-arches', 'name': '麦加利银行襄理住宅花园侧双石券与中柱', 'viewer_page': 'chartered-bank-garden-twin-arches.html', 'scope': '江苏路796号花园侧相连的两个石拱，自原照取可见柱段、粗砌券石、拱肩和上部抹灰栏板。', 'model_scope_zh': '花园侧两座券洞、共用中柱与上沿栏板', 'interiors_modeled': False, 'status': 'photograph-based-architectural-detail', 'coordinate_convention': 'X across garden elevation, Y towards interior, Z upright. The lower cut is within the visible pier, above the unknown ground level.', 'source_register': 'source/precise/changning-chartered-bank-garden-twin-arches/reference-review.json', 'estimated': '以照片中的单券净跨约2.4米作比例估算；石材色和进深属近似值。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['CHARTERED_ARCADE_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
