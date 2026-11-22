"""Export the photographed south portal in Lane 379 of Fuzhou Road."""
from argparse import ArgumentParser
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from south_portal import PALETTE, install

ID = 'huangpu-jiangsu-inn-south-portal'
SCOPE = '福州路379弄50号原江苏旅社南面中央一开间，依2015年至2019年刊发照片制作50号绿牌、打开的铁门、柱头、木格窗、花饰和阶梯式山花。福州路沿街楼、邻弄、院内雕花廊、其余屋脊和住户室内保留在本次范围之外。'
META = {'id': ID, 'name': '江苏旅社弄内南门与山花', 'viewer_page': 'jiangsu-inn-south-portal.html',
        'status': 'photo-informed-historic-lane-elevation', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': '照片约束构件比例；净门宽、地板高差、前后进深和颜色为估计。航片提供南墙檐线和轴线，旧照无法还原室内。', 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. X follows the south wall eastward, Y points into the house. The model base is street grade.',
        'copyright': 'Original geometry under MIT. Source photographs remain with their credited photographers.'}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['JIANGSU_PORTAL_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, install)
