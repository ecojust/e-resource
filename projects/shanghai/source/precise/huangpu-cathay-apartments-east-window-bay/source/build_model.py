"""Package the east street bay of the southern Cathay Apartments block."""
from argparse import ArgumentParser
import os
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from east_bay import PALETTE,add_bay
ID='huangpu-cathay-apartments-east-window-bay'
NAME='国泰公寓南楼东端临街窗组与砖檐'
SCOPE='4C003国泰公寓南楼。院口西侧最东一组二至四层四联直窗、褐砖、仿石转角、可见金属栏架和短檐。'
META=dict(id=ID,name=NAME,viewer_page='cathay-apartments-east-window-bay.html',status='photo-informed-cathay-apartments-east-window-bay',scope=SCOPE,model_scope_zh=SCOPE,
          source_register='source/precise/'+ID+'/reference-review.json',
          estimated='两处街站与原城东南角对齐，沿街宽约5.5米；窗与屋檐高度约有0.5至0.9米误差，栏架出挑为照片估计。',
          interiors_modeled=False,coordinate_convention='Local metres. X runs ENE along Huaihai Middle Road; Y goes into the south apartment block. Z is height above the adjacent pavement.',
          copyright='Original mesh and procedurally drawn brick texture under MIT. Source photographs retain their credits.')
if __name__=='__main__':
    parser=ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['CATHAY_BAY_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_bay)
