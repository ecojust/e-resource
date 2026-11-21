"""Export the southeast corner tower of the former Shanghai–Nanking Railway offices."""
from argparse import ArgumentParser
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from railway_corner import PALETTE, add_building

ID = 'huangpu-yuanfang-lane-railway-corner'
SCOPE = '依上海市人民政府1999年原牌、Livelikerw的2015年街照及2022年记者入弄采访，取元芳弄北侧东端一栋的东南折角塔楼上部。两侧分别建圆券、铁栏小阳台和上层成对方窗，中央为无窗折面；砖带和深色压顶沿三面转折。尺寸、颜色、窗扇细节及后部截口按照片估配。其余各翼、脚手架、遮挡下部及室内留待有据时补充。'
META = {'id': ID, 'name': '元芳弄原沪宁铁路局东南角塔楼', 'viewer_page': 'yuanfang-railway-corner.html',
        'status': 'photo-informed-public-street-elevation', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. The south face looks over Yuanfang Lane to local negative Y. The cross lane lies towards local positive X. The occupied block extends west and north of the chamfer.',
        'copyright': 'Original geometry under MIT. Source photographs remain with their credited photographers.'}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['YUANFANG_CORNER_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
