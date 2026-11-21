"""Package the documented Ningbo Road front and street chamfer of the Strand Theatre."""
import argparse
import os
import sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from theatre_front import PALETTE,add_building
ID='huangpu-strand-theatre-ningbo-front'
SCOPE='1930年新光大戏院宁波路586号南立面与东端折角，含大圆券、两侧联窗、红黄菱格砖、螺旋壁柱、波纹檐及2024年改为酒店后可见的入口。'
META=dict(id=ID,name='新光大戏院宁波路圆券与菱格砖立面',viewer_page='strand-theatre-ningbo-front.html',scope=SCOPE,model_scope_zh=SCOPE,status='photo-informed-street-frontage',source_register=f'source/precise/{ID}/reference-review.json',estimated='南墙注册边20.81米，东端折角4.56米。主体高度由宁波路2020年两站与2021年路口街景约束。退后的顶层窗、檐口和圆券纵深结合2015与2024年实拍估计。',coordinate_convention='Metres. X follows Ningbo Road from the west end toward the chamfer, Y points into the former theatre and Z is up. The origin is the southwestern corner of signed building 681.',interiors_modeled=False,copyright='Original MIT geometry and procedurally painted brick. Referenced photographs are credited separately.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    args,other=parser.parse_known_args()
    os.environ['STRAND_BLENDER']=args.blender
    sys.argv[1:]=[*other,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
