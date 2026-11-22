"""Reconstruct the rounded street walls at 115 Middle Jiangxi Road."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
sys.path[:0] = [str(SOURCE), str(SOURCE.parents[3] / 'tools')]
from package_architectural_model import build
from hengye_corner import PALETTE, add_building

ID = 'huangpu-hengye-li-jiangxi-corner'
SCOPE = '2019、2021年照片可见的恒业里江西中路115号圆街角与临两街短段。制作三层灰砖、两排上层券窗、泗泾路一层券窗、江西中路近角方口与连续红砖腰线。楼后原体量、完整屋顶和弄内各宅另列。'
META = {
    'id': ID, 'name': '恒业里江西中路115号泗泾路转角',
    'viewer_page': 'hengye-li-jiangxi-corner.html', 'scope': SCOPE, 'model_scope_zh': SCOPE,
    'status': 'photo-informed-street-facade', 'source_register': f'source/precise/{ID}/reference-review.json',
    'estimated': '街线来源为建筑轮廓。圆角半径、层高、窗深及店面宽度按影像比例估计。',
    'coordinate_convention': 'Metres and Z up. Local X follows the Sijing Road front eastward, local Y into the building.',
    'interiors_modeled': False, 'copyright': 'Original mesh and procedural brick materials, MIT. Reference photographs credited in the source register.',
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    flags, remaining = parser.parse_known_args()
    os.environ['HENGYE_CORNER_BLENDER'] = flags.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
