"""Export the east-facing south pavilion and doorway of the Mitsui Bussan building."""
from argparse import ArgumentParser
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from pediment_front import PALETTE, add_building

ID = 'huangpu-mitsui-bussan-pediment-front'
SCOPE = '依据2013年12月19日四川中路街照、1908年出版的历史图版及Virtual Shanghai所藏街景，制作福州路口北侧红砖东立面的南端。模型含白石隅、底层及二层双洞、三层三连拱和三角山花、临街石门罩及上方窗列。建筑尺度、门扇和砖石纹样按照片比例估计。'
META = {'id': ID, 'name': '三井洋行四川中路东立面南端山花与入口', 'viewer_page': 'mitsui-bussan-pediment-front.html',
        'status': 'photo-informed-public-street-elevation', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. The east street frontage faces local negative Y. Local positive X runs northward along Sichuan Middle Road.',
        'copyright': 'Original architectural geometry, MIT. Source photographs are credited in the reference register.'}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['MITSUI_BUSSAN_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
