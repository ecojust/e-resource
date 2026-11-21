"""Build the Bund Signal Tower at its relocated Shanghai waterfront site."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from tower import PALETTE, add_building

ID = 'huangpu-bund-signal-tower'
SCOPE = '1993年整体东南平移后的外滩信号台现址。按实照制作西北端圆柱塔基、双层站房、平台、三段红砖腰带、杆顶风向仪和横桁；门窗构造和不可见部位据照片估算。'
META = dict(id=ID,name='外滩信号台（现址塔身、号杆与站房）',status='photo-informed-relocated-signal-station',viewer_page='bund-signal-tower.html',scope=SCOPE,model_scope_zh=SCOPE,source_register='source/precise/'+ID+'/reference-review.json',interiors_modeled=False,all_dimensions_estimated=True,coordinate_convention='Metres, Z up. +Y points along the station house towards its tower at the northwestern end.',copyright='Original architectural mesh under MIT. Reference photographs are not embedded.')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['BUND_SIGNAL_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
