"""Build the documented exterior of the entrance marked 124 on Nanchang Road."""
from argparse import ArgumentParser
from pathlib import Path
import os
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from portal import PALETTE,add_portal

ID='huangpu-park-terrace-nanchang-124-portal'
NAME='花园住宅群南昌路124号半圆券门与街柱'
SCOPE='南昌路124号半圆券套、后门气窗与前方带124牌的方墩、另一侧界柱及暗色街门。'
META=dict(id=ID,name=NAME,viewer_page='park-terrace-nanchang-124-portal.html',
          status='photo-informed-nanchang-124-entrance',scope=SCOPE,model_scope_zh=SCOPE,
          source_register='source/precise/'+ID+'/reference-review.json',interiors_modeled=False,
          estimated='门券顶约4.0米，两街柱约2.5和2.6米。2020及2023街站的定位和高度差约0.2至0.5米；门板厚度、门后阴影深度是估计值。',
          coordinate_convention='Metres. Origin below the front arch crown. X follows Nanchang Road east-northeast. Y is inward and Z is height above the pavement.',
          copyright='Original model MIT. The documentary photographs retain their original credits. Noto Sans CJK SC subset licensed under SIL OFL 1.1.')
if __name__=='__main__':
    args=ArgumentParser(add_help=False)
    args.add_argument('--blender',default='blender')
    settings,other=args.parse_known_args()
    os.environ['NANCHANG_124_BLENDER']=settings.blender
    sys.argv[1:]=[*other,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_portal)
