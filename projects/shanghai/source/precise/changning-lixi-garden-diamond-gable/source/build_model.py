"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META=dict(id='changning-lixi-garden-diamond-gable',name='利西路花园住宅菱形砖饰山墙与方烟囱',viewer_page='lixi-garden-diamond-gable.html',scope='根据长宁区规资局标明利西路30、32号的一张照片，制作图左深色菱饰的红砖山墙及其右侧方烟囱。',model_scope_zh='山花砖菱、双窗和烟囱顶',interiors_modeled=False,status='photograph-based-architectural-detail',coordinate_convention='X across the gable, Y toward the roof and Z up.',source_register='source/precise/changning-lixi-garden-diamond-gable/reference-review.json',estimated='山墙净宽暂取4.5米。照片同列30和32号，无法独立给画面左侧山墙指定其中一个门牌。窗脚以下和完整屋面未测绘。')
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['LIXI_DIAMOND_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
