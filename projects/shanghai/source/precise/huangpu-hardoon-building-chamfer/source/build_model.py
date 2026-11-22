"""Export the photographed southeast chamfer of the Hardoon Building."""
from argparse import ArgumentParser
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from hardoon_chamfer import PALETTE, add_building

ID = 'huangpu-hardoon-building-chamfer'
SCOPE = '按市房管局第三批3A017、2014年路口实照与2020年上海规划资源“东南角”照片，取南京东路和四川中路交口切角一跨。自底商檐线上方起建灰砖墙、宽拱窗、弧形栏板、上层拱窗和红浅双色曲线老虎窗。高度、截口与色彩按照片和原城屋檐估配。两条长翼、底商、内院及114号纪念边门沿用原城。'
META = {'id': ID, 'name': '哈同大楼（慈安里大楼）东南转角立面', 'viewer_page': 'hardoon-building-chamfer.html',
        'status': 'photo-informed-public-street-elevation', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. The corner street elevation faces local negative Y. X runs from the Nanjing East Road end to the Sichuan Middle Road end. Ground-floor retail lies below the model.',
        'copyright': 'Original geometry under MIT. Source photographs remain with their credited photographers.'}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['HARDOON_CHAMFER_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
