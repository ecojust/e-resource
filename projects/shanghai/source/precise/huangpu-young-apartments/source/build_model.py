"""Build the curved Young Apartments facade at Huaihai and Yandang Roads."""
import argparse
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from young_corner import PALETTE, add_young_corner

ID = 'huangpu-young-apartments'
SCOPE = '据2006年实照、2014年实名照片、街景及上海市银行博物馆的成楼档案，制作淮海中路与雁荡路交叉口的银行圆角、三层栏窗、顶层玻璃日光室与重檐屋面。两条街翼仅延伸至相邻窗组。'
META = dict(id=ID, name='永业大楼（杨氏公寓）淮海中路、雁荡路圆角', status='original-photo-informed-partial-exterior',
            viewer_page='young-apartments.html', scope=SCOPE, model_scope_zh=SCOPE,
            interiors_modeled=False, source_register=f'source/precise/{ID}/reference-review.json',
            estimated='楼角半径由实名地块平面和航片估算。垂直尺寸按三处街景及照片比例估算，立面装饰为原创建模。',
            coordinate_convention='Local origin at the mapped corner arc centre. +X towards the Huaihai Road side, +Y into the block and +Z up.',
            copyright='Original MIT geometry and materials. Historic and modern photographs are cited by URL.')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['YOUNG_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_young_corner)
