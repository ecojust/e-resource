"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META=dict(id='changning-lianan-pierced-balustrade-panel',name='联安坊老住宅阳台水泥透花栏板',viewer_page='lianan-pierced-balustrade-panel.html',scope='长宁区规资局公开照片中一段阳台透花栏板的单个纹样。取中间细长孔和两侧上下卷叶孔，只做装饰板本体。',model_scope_zh='单片水泥透花及板上、下线脚',interiors_modeled=False,status='photograph-based-architectural-detail',coordinate_convention='X across the ornamental repeat, Y behind its front surface, Z upright.',source_register='source/precise/changning-lianan-pierced-balustrade-panel/reference-review.json',estimated='照片中纹样约31×30个原图像素。可辨的五个暗孔沿轮廓离散重绘，板宽、深度和背面按比例估计。')
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['LIANAN_PLASTER_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
