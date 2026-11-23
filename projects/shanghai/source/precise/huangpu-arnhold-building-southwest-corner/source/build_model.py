"""Package the street-front portions of the former Arnhold Building in Shanghai."""
import argparse
import os
import sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from arnhold_front import PALETTE,add_building
ID='huangpu-arnhold-building-southwest-corner'
SCOPE='安利大楼面向四川中路、九江路的西南转角、320号灰白券门、九江路石券门和两侧邻近的红砖窗带。以2023年蓝色角部弧带为准。'
META=dict(id=ID,name='安利大楼西南转角入口与两街红砖窗带',viewer_page='arnhold-building-southwest-corner.html',scope=SCOPE,model_scope_zh=SCOPE,status='photo-informed-street-frontage',source_register=f'source/precise/{ID}/reference-review.json',estimated='原城足印、四台街景摄影点与两街入口对齐。实墙至檐顶约26.59米，金属屋顶围栏约27.30米。窗深、门龛和各肩部厚度依照片估计。',coordinate_convention='Metres. X follows Jiujiang Road toward the east. Y points inland. Origin is the south end of the former footprint chamfer.',interiors_modeled=False,copyright='Original MIT geometry and procedural red brick texture. Noto Sans CJK SC typeface subset under SIL OFL 1.1. Reference photographs are separately credited.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    args,other=parser.parse_known_args()
    os.environ['ARNHOLD_BLENDER']=args.blender
    sys.argv[1:]=[*other,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
