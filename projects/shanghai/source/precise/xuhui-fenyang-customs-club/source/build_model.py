"""Export the wood house of the Customs Club at No. 3, Lane 9 Fenyang Road."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from club_geometry import PALETTE, add_building

ID = 'xuhui-fenyang-customs-club'
SCOPE = '重建汾阳路9弄3号海关俱乐部木屋的花园南廊、方柱、中央台阶及屋顶。南面一座多面凸出的翘檐老虎窗，东侧两窗与西侧窗、方形尖塔均有2017至2020年照片和现场保护牌可核。其他立面及尺寸按照片与航片估算。'
META = {'id': ID, 'name': '海关俱乐部木屋', 'viewer_page': 'fenyang-customs-club.html',
        'status': 'original-photo-informed-exterior', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False,
        'coordinate_convention': 'Metres, Z up. Local X follows the roof east-northeast. The garden front faces negative local Y.',
        'copyright': 'Original architectural geometry, MIT. External photographs and plans are reference material; no third-party image is embedded.'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['FENYANG_CUSTOMS_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
