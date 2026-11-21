"""Package the historic east building of the Shanghai Butterfield & Swire riverside office."""
import argparse
import os
import sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from river_front import PALETTE,add_building
ID='huangpu-swire-east-building-bund-front'
SCOPE='1906年太古洋行东楼中山东二路22号临黄浦江七开间，含中轴门券、两组双联拱窗、铁栏、砖纹和顶端山花；依据2022年竣工后的临街玻璃状况。'
META=dict(id=ID,name='太古洋行东楼临江七开间红砖正立面',viewer_page='swire-east-building-bund-front.html',scope=SCOPE,model_scope_zh=SCOPE,status='photo-informed-street-frontage',source_register=f'source/precise/{ID}/reference-review.json',estimated='注册边宽30.76米。按2011年有焦距纪录的实照标定石窗台、窗头和檐线，2022年竣工照核当前窗料。墙后接缝、窗内进深和铁件截面按可见轮廓估计。',coordinate_convention='Metres. X follows the riverside frontage from south to north, Y extends into the east building and Z is up. The origin is the southern cadastral corner on Zhongshan Dong Er Road.',interiors_modeled=False,copyright='Original MIT geometry and procedurally painted brick. Referenced photographs are credited separately.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    args,other=parser.parse_known_args()
    os.environ['SWIRE_BLENDER']=args.blender
    sys.argv[1:]=[*other,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
