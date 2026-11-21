"""Rebuild the east street facade and tower of the Lyceum Building."""
import argparse
import os
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))

from package_architectural_model import build
from street_front import PALETTE, add_building

ID = 'huangpu-rockbund-lyceum-building'
SCOPE = '圆明园路185号临街塔楼、两层券窗与三角窗楣、双语石门额和向北的砖翼，依据2014年现场照片与洛克外滩源修缮项目的东立面图和街景。'
META = dict(id=ID, name='兰心大楼圆明园路入口塔楼与东立面', viewer_page='rockbund-lyceum-building.html',
            status='photograph-and-conservation-elevation-informed', model_scope_zh=SCOPE, scope=SCOPE, reference_height_m=35.45,
            estimated='东侧地块边约30.75米。各层标高用图上25米图例和当前街墙配准；短侧返、露台纵深和石饰厚度为照片估值。',
            source_register=f'source/precise/{ID}/reference-review.json', interiors_modeled=False,
            coordinate_convention='Metres, source Z up, local positive X north along the east street facade, positive Y into the building.',
            copyright='Original architectural geometry and running-bond texture, MIT. Door typeface uses the bundled OFL subset.')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remainder = parser.parse_known_args()
    os.environ['LYCEUM_FRONT_BLENDER'] = options.blender
    sys.argv[1:] = [*remainder, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
