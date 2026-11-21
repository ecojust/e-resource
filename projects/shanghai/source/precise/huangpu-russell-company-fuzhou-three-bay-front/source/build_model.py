"""Package the street-front portions of the Russell Company building on Fuzhou Road."""
import argparse
import os
import sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from russell_front import PALETTE,add_building
ID='huangpu-russell-company-fuzhou-three-bay-front'
SCOPE='福州路17、19号旗昌洋行旧址北面东段三开间石墙、底层圆券、上层尖券与可见凸窗、平台铁栏和台阶。'
META=dict(id=ID,name='旗昌洋行福州路三开间石墙与尖券窗',viewer_page='russell-company-fuzhou-three-bay-front.html',scope=SCOPE,model_scope_zh=SCOPE,status='photo-informed-street-frontage',source_register=f'source/precise/{ID}/reference-review.json',estimated='按独立2015原片和2021三台摄影点对照。可见檐口高约11.2米，平台与室外地面有高差，檐顶、窗凸出及背部衔接深度依照片估测。',coordinate_convention='Metres. X runs west along Fuzhou Road. Y points inward and Z up. Origin is the east cadastral corner beside the separate China Merchants building.',interiors_modeled=False,copyright='Original MIT geometry and procedural stone texture. Referenced photographs are credited separately.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    args,other=parser.parse_known_args()
    os.environ['RUSSELL_BLENDER']=args.blender
    sys.argv[1:]=[*other,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
