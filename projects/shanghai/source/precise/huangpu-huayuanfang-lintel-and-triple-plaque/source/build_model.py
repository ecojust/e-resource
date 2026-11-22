"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-huayuanfang-lintel-and-triple-plaque', 'name': '花园坊瑞金二路三字额与叠梁弄门', 'viewer_page': 'huayuanfang-lintel-and-triple-plaque.html', 'scope': '取瑞金二路沿街主弄门两柱、叠级门楣、上方通长三字题额及两端竖向凹线，题额按照片从右到左读作花園坊。', 'model_scope_zh': '取瑞金二路沿街主弄门两柱、叠级门楣、上方通长三字题额及两端竖向凹线，题额按照片从右到左读作花園坊。', 'interiors_modeled': False, 'status': 'photographed-street-elevation-fragment', 'coordinate_convention': 'X follows the photographed facade, Y increases backwards, Z is up.', 'source_register': 'source/precise/huangpu-huayuanfang-lintel-and-triple-plaque/reference-review.json', 'estimated': '按门洞净宽约2.70米推算。题额笔画按正照轮廓概括，门柱背面及檐顶止于题名墙所在的一跨。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['HUAYUANFANG_GATE_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
