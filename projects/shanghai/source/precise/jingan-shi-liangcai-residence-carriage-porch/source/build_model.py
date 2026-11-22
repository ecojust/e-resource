"""Export the round-fronted carriage porch of Shi Liangcai's Tongren Road residence."""
from argparse import ArgumentParser
from pathlib import Path
import os
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from carriage_porch import PALETTE, add_building

ID = 'jingan-shi-liangcai-residence-carriage-porch'
SCOPE = '铜仁路257号院内南部主楼的外挑车廊，含正面与南北两侧通券、花饰方墩、弧形楼层出挑、三幅花饰板、红棕百叶、上层圈线及红色压顶。侧悬窗、主宅其余屋顶与北附楼沿原城保留。'
META = {
    'id': ID, 'name': '史量才旧居（铜仁路257号）院内主楼圆首券拱车廊',
    'viewer_page': 'shi-liangcai-carriage-porch.html',
    'status': 'photo-informed-garden-residence-porch', 'model_scope_zh': SCOPE, 'scope': SCOPE,
    'estimated': '高度、券口宽、花板细纹依据两位作者的相反方向照片估配。航片所见曲首的平面尺寸有释读误差。',
    'source_register': 'source/precise/'+ID+'/reference-review.json',
    'interiors_modeled': False,
    'coordinate_convention': 'Metres, Z up. The photo-visible projecting end faces local negative Y; the south and north side openings span the X axis. The rear attachment is Y=0.',
    'copyright': 'Original geometric reconstruction under MIT. Documentary photographs are credited to their photographers and are not embedded.',
}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['SHI_TONGREN_PORCH_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
