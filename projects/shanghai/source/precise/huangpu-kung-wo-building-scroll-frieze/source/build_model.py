"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-kung-wo-building-scroll-frieze', 'name': '公和洋行大楼切角圆章与卷草檐带', 'viewer_page': 'kung-wo-building-scroll-frieze.html', 'scope': '取2015年具名照片中切角正面并列的两方圆章、相邻街面可见的四方卷草板，以及下方带横线的浅色墙身、左邻窗上段和右侧阴影中的托檐。', 'model_scope_zh': '取2015年具名照片中切角正面并列的两方圆章、相邻街面可见的四方卷草板，以及下方带横线的浅色墙身、左邻窗上段和右侧阴影中的托檐。', 'interiors_modeled': False, 'status': 'independent-photograph-based-facade-detail', 'coordinate_convention': 'X follows the photographed street elevation, Y recedes into the front wall, Z is up.', 'source_register': 'source/precise/huangpu-kung-wo-building-scroll-frieze/reference-review.json', 'estimated': '中央两方饰板总宽暂设1.9米，纹饰深度与侧面转角均按照片比例估计。截面止于可辨的上檐和窗上段。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['KUNGWO_FRIEZE_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
