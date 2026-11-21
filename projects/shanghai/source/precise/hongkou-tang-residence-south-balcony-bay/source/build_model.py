"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from tang_porch import PALETTE,model
META={'id': 'hongkou-tang-residence-south-balcony-bay', 'name': '原汤公馆南门廊中跨弧形阳台与双柱', 'viewer_page': 'tang-residence-south-balcony-bay.html', 'scope': '四川北路2023弄35号南门廊的两根中央通高石柱、科林斯式柱头、弧形阳台石边及铁花栏杆，并表现其后可见的红褐色木窗。', 'model_scope_zh': '四川北路2023弄35号南门廊的两根中央通高石柱、科林斯式柱头、弧形阳台石边及铁花栏杆，并表现其后可见的红褐色木窗。', 'interiors_modeled': False, 'status': 'independent-historic-fragment', 'coordinate_convention': 'Metres. X viewed from the garden is rightward, Y recedes into the porch and Z is upwards.', 'source_register': 'source/precise/hongkou-tang-residence-south-balcony-bay/reference-review.json', 'estimated': '尺寸按斜向外观照片的比例估算。两层通高、四柱与阳台形式可由区级档案和第二张照片交叉确认。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['TANG_PORCH_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
