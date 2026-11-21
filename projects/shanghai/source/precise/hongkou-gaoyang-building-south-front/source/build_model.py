"""Package the south entrance and twin lanterns at 817 East Daming Road."""
from pathlib import Path
import argparse
import os
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from gaoyang_facade import PALETTE, add_gaoyang

IDENT='hongkou-gaoyang-building-south-front'
SCOPE='高阳大楼临东大名路的五层南立面、中央退进门廊及两座塔亭。根据档案照片和现状制作街侧窗列、券窗、宝瓶栏杆与可见两端侧面。'
META=dict(id=IDENT,name='高阳大楼东大名路双塔正立面',status='original-photo-informed-historic-exterior',
          viewer_page='gaoyang-building-south-front.html',scope=SCOPE,model_scope_zh=SCOPE,
          interiors_modeled=False,source_register=f'source/precise/{IDENT}/reference-review.json',
          estimated='面宽、退进取自原街墙，窗高、双塔、柱列、旗杆和短侧翼深度均根据公开照片估算。',
          coordinate_convention='Local +X eastward along East Daming Road, +Y northward into the lot, +Z up.',
          copyright='Original MIT geometry. Reference photographs and imagery are credited individually.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['GAOYANG_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_gaoyang)
