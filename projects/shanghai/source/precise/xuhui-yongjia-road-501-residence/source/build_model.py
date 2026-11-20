"""Rebuild the three photographed elevations of the 501 Yongjia Road residence."""
from pathlib import Path
import argparse
import os
import sys

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC.parents[3] / 'tools'))
from package_architectural_model import build
from villa import PALETTE, villa

ID = 'xuhui-yongjia-road-501-residence'
SCOPE = ('永嘉路501号花园住宅的临街北立面、圆锥铁皮顶的西北塔、西端低附间、南向花园长墙和对应坡瓦屋面。'
         '东端未能复核的一段、园区、隔院岳阳路145号住宅及室内另列。')
META = {
    'id': ID, 'name': '永嘉路501号住宅北街面、圆塔与花园立面',
    'status': 'original-photo-informed-exterior', 'viewer_page': 'yongjia-road-501.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{ID}/reference-review.json',
    'estimated': '按2014年1月街照、天平街道两张旧照、杨浦图书馆塔楼照与19级航片对位。墙高、塔径和细部按比例估算。',
    'coordinate_convention': 'Local X follows the northern facade west toward the circular tower. Y goes south, into the garden, and Z is up.',
    'copyright': 'Original geometry and materials, MIT. External photographs are referenced by source.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, rest = parser.parse_known_args()
    os.environ['YONGJIA501_BLENDER'] = options.blender
    sys.argv[1:] = [*rest, '--blender', str(SRC / 'blender_preview.py')]
    build(SRC, META, PALETTE, villa)
