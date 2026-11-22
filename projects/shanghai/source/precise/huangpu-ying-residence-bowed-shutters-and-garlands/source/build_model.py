"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-ying-residence-bowed-shutters-and-garlands', 'name': '应公馆园侧弧形百叶凸窗与垂花窗裙', 'viewer_page': 'ying-residence-bowed-shutters-and-garlands.html', 'scope': '取园侧右端凸窗的一层双组深色百叶、窗下两串垂花、两侧竖带和上方弧形小阳台瓶栏。', 'model_scope_zh': '取园侧右端凸窗的一层双组深色百叶、窗下两串垂花、两侧竖带和上方弧形小阳台瓶栏。', 'interiors_modeled': False, 'status': 'photographed-street-elevation-fragment', 'coordinate_convention': 'X follows the photographed facade, Y increases backwards, Z is up.', 'source_register': 'source/precise/huangpu-ying-residence-bowed-shutters-and-garlands/reference-review.json', 'estimated': '依门窗习惯尺寸估算两开间总弧长约3.60米。墙后进深、瓶栏背面和被树遮挡的叶片由可见边界估计；地面层、山墙和中部敞廊保留在取景范围以外。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['YING_RESIDENCE_BAY_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
