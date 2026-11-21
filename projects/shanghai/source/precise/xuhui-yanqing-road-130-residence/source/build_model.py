"""Export the courtyard front of the listed house at 130 Yanqing Road."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from yanqing_geometry import PALETTE, add_building

ID = 'xuhui-yanqing-road-130-residence'
SCOPE = '复原延庆路130号院内南立面的前凸弧形主厅、前庭石阶、花盆栏板、上层双端弧形山墙与后退的红瓦坡屋面。1928年建造年代、外观与位置据市级名录、1948年行号图、2016年实照及徐汇区文旅资料。各构件尺寸、冠饰浮雕与部分窗格按照片比例估计。北部屋面、附房和院门保留现状底模。'
META = {'id': ID, 'name': '延庆路130号住宅南向庭院立面', 'viewer_page': 'yanqing-road-130.html',
        'status': 'original-photo-informed-exterior', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False,
        'coordinate_convention': 'Metres, Z up. Local X follows the long front toward east-northeast. Negative local Y faces the garden, about 155 degrees from true north.',
        'copyright': 'Original architectural geometry, MIT. External photographs and plans are reference material; no third-party image is embedded.'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['YANQING_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
