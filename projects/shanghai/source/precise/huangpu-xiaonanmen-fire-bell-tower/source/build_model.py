"""Reconstruct the four-legged concrete fire alarm tower in the courtyard at 581 Zhonghua Road."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
sys.path.insert(0,str(SOURCE.parents[1]/'hongkou-general-post-office/source/common'))
from package_architectural_model import build
from tower_frame import build_frame
from lookout import stair, watch_room
from tower_finish import PALETTE, apply

ID='huangpu-xiaonanmen-fire-bell-tower'
META={
    'id':ID,
    'name':'小南门警钟楼四足塔架与瞭望室',
    'viewer_page':'xiaonanmen-fire-bell-tower.html',
    'scope':'中华路581号院内的四足火警塔，含拱脚、逐层收分的斜柱、交叉铁撑、铁笼旋梯、瞭望室与屋顶栏。',
    'model_scope_zh':'参照2016至2020年塔体外观。沿街入口、相邻救火联合会办公楼及原已佚的警钟另记。',
    'status':'photo-measured historic structure',
    'source_reference_only':True,
}


def add_geometry(builder,lod):
    build_frame(builder,lod)
    stair(builder,lod)
    watch_room(builder,lod)
    apply(builder)


if __name__=='__main__':
    import argparse
    import os
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, rest = parser.parse_known_args()
    os.environ['XIAONANMEN_BLENDER'] = options.blender
    sys.argv[1:] = [*rest, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_geometry)
