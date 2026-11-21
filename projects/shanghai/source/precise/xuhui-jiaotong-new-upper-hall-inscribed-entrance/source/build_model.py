"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from inscribed_portal import PALETTE,add_portal
META={'id': 'xuhui-jiaotong-new-upper-hall-inscribed-entrance', 'name': '交通大学徐汇校区新上院题名门廊', 'viewer_page': 'jiaotong-new-upper-hall-inscribed-entrance.html', 'scope': '新上院南立面的题名横匾、叠檐、花饰石墩、曲线托角、三门木作与前方四道踏步。', 'interiors_modeled': False, 'status': 'photo-measured-entrance', 'coordinate_convention': 'Metres. X increases east along the photographed south wall. Y increases north into the portico, with the stone pier face at zero. Z is above the forecourt.', 'source_register': 'source/precise/xuhui-jiaotong-new-upper-hall-inscribed-entrance/reference-review.json', 'estimated': '总宽以校方南立面测绘图与底图轮廓估算；高度、凹进、花纹深度、灯具尺度与字形按修缮图19和2008年侧照比例重绘。', 'copyright': 'Independent geometric reconstruction. Source photographs and campus drawings remain separately credited.', 'model_scope_zh': '新上院南立面的题名横匾、叠檐、花饰石墩、曲线托角、三门木作与前方四道踏步。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['NEW_UPPER_HALL_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_portal)
