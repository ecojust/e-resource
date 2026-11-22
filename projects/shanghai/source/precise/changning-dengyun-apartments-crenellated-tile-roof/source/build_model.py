"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'changning-dengyun-apartments-crenellated-tile-roof', 'name': '登云公寓翼楼红瓦坡顶与齿形女儿墙', 'viewer_page': 'dengyun-apartments-crenellated-tile-roof.html', 'scope': '区规资局俯摄图中，左翼凸出转角的红瓦坡顶、四周浅色齿形女儿墙与下层挑檐托。', 'model_scope_zh': '区规资局俯摄图中，左翼凸出转角的红瓦坡顶、四周浅色齿形女儿墙与下层挑檐托。', 'interiors_modeled': False, 'status': 'photograph-based-architectural-detail', 'coordinate_convention': 'X follows the principal visible elevation, Y recedes into the roof and Z points up.', 'source_register': 'source/precise/changning-dengyun-apartments-crenellated-tile-roof/reference-review.json', 'estimated': '屋面平面和高度取自两个相交檐面的相对比例。背后受遮挡的坡度、材料厚度与绝对尺寸为估计。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['DENGYUN_CORNICE_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
