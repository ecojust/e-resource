"""Export the open Jiujiang Road arcade and documented roof front of Carlowitz & Co.."""
import argparse
import json
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
import package_architectural_model as packaging
from carlowitz_geometry import PALETTE, add_building

ID = 'huangpu-carlowitz-jiujiang-front'
SCOPE = '按1908年出版的洋行全景、2013年九江路实照和市文化旅游局2022年刊发的外景与廊内照，制作九江路四层红砖券窗、透空石栏、三座双窗山花、四个较低的老虎窗及江西中路近端圆角。底层按修缮后照片开放外廊。屋面、进深与构造尺寸据影像估计，完整江西中路侧墙与北部面貌保留原图。'
META = {'id': ID, 'name': '礼和洋行九江路街面', 'viewer_page': 'carlowitz-jiujiang-front.html',
        'status': 'original-photo-informed-exterior', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False,
        'coordinate_convention': 'Metres, Z up. Local X runs east-northeast along Jiujiang Road; negative local Y faces the roadway, about 164 degrees clockwise from north.',
        'copyright': 'Original architectural geometry, MIT. External photographs and plans are reference material; no third-party image is embedded.'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['CARLOWITZ_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    # This detailed street elevation has many rail spindles. Stream the intermediate
    # parts file with full-precision coordinates so its pretty-print whitespace
    # does not consume as much temporary space as the three published meshes.
    write_receipt = packaging.write_json
    def write_json(path, value):
        if path.name == 'parts.json':
            with path.open('w', encoding='utf-8') as stream:
                json.dump(value, stream, ensure_ascii=False, separators=(',', ':'))
        else:
            write_receipt(path, value)
    packaging.write_json = write_json
    packaging.build(SOURCE, META, PALETTE, add_building)
