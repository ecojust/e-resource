"""Build the grey stone corner at 161 East Nanjing Road from its documented openings."""
from pathlib import Path
import argparse
import os
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from meilun_facade import PALETTE, add_meilun

IDENT = 'huangpu-meilun-west-nanjing-corner'
SCOPE = '美伦大楼西楼临南京东路和江西中路的西北转角。复建两侧店面、斜角凹入入口、上下山花、石墩和檐顶栏杆。'
META = dict(id=IDENT, name='美伦大楼西楼南京东路西北转角',
            status='original-photo-informed-historic-exterior',
            viewer_page='meilun-west-nanjing-corner.html', scope=SCOPE, model_scope_zh=SCOPE,
            interiors_modeled=False, source_register=f'source/precise/{IDENT}/reference-review.json',
            estimated='临街走向和转角两端从具名底图量取。层高、商铺退进和石作深度以照片比例估算。',
            coordinate_convention='Local +X follows East Nanjing Road east. +Y faces the street. +Z is up.',
            copyright='Original geometry under the MIT license. Photograph credits appear in the source register.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, rest = parser.parse_known_args()
    os.environ['MEILUN_BLENDER'] = options.blender
    sys.argv[1:] = [*rest, '--blender', str(HERE / 'blender_preview.py')]
    build(HERE, META, PALETTE, add_meilun)
