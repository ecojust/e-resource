"""Build the post-restoration Picardie Apartments south front and entrance canopy."""
import argparse
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from south_front import PALETTE, add_south_front

ID = 'xuhui-picardie-apartments-south-front'
SCOPE = ('依据2023年修缮完成后的正面、入口及雨篷底部照片制作南花园侧的阶梯塔楼、两列深阳台、'
         '浅色侧翼窗列、534号黑色方砖基座、三樘入口和二层标高的悬挑雨篷。两侧沿街长翼、后部与室内另列。')
META = dict(id=ID, name='毕卡迪公寓南向阶梯塔楼与534号入口', status='original-photo-informed-partial-exterior',
            viewer_page='picardie-apartments.html', scope=SCOPE, model_scope_zh=SCOPE,
            interiors_modeled=False, source_register=f'source/precise/{ID}/reference-review.json',
            estimated='原地块南边与独立酒店门牌点控制位置。楼层、外观和修缮分期见市住建委照片；高度、开间和进深为估值。',
            coordinate_convention='Local +X follows the south garden front toward east, +Y enters the building toward north, +Z is up.',
            copyright='Original MIT geometry and materials. Documentary photographs are cited by URL.')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['PICARDIE_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_south_front)
