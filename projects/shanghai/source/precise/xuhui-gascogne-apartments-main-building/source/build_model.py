"""Build the garden-facing elevation of the 1935 Gascogne apartment tower."""
from pathlib import Path
import argparse
import os
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from apartment import PALETTE,build_apartments
ID='xuhui-gascogne-apartments-main-building'
SCOPE='1935年盖司康公寓十三层主楼南向前院的阶梯立面、轴线三道白色竖带、两组双列内凹阳台、黑色底层双入口及浅色弧角雨篷石阶。'
META=dict(id=ID,name='盖司康公寓主楼南向前院立面',viewer_page='gascogne-apartments-main.html',scope=SCOPE,model_scope_zh=SCOPE,
          status='photographed-thirteen-storey-garden-elevation',source_register='source/precise/'+ID+'/reference-review.json',
          estimated='庭院侧宽49.26米按底图107推定。建筑史记主楼13层、约53米；阳台、窗格、罩棚、端翼退台与石阶按1937年及现代照片估计。前方淮海中路1204–1218号五层辅楼另有独立登记。',interiors_modeled=False,
          coordinate_convention='Author X east along the main south wall; Y into the building; Z up. glTF +Z faces the entrance court.',
          copyright='Original geometry and materials under MIT. Reference photographs linked separately.')
if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    args,remaining=options.parse_known_args()
    os.environ['GASCOGNE_MAIN_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,build_apartments)
