"""Reconstruct the photographed No. 3 gateway and terrace at Dafu Li."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if (p / 'tools/package_architectural_model.py').is_file())
sys.path.append(str(PROJECT / 'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
from court_three import PALETTE as GATE, add_no3
from court_terrace import PALETTE as TERRACE, add_terrace

ID = 'xuhui-dafuli-yanqing-29-no3-court'
SLUG = 'dafuli-yanqing-29-no3-court'
PALETTE = {**GATE, **TERRACE}
FRONT_Y = .65
WALL_Y = 1.359
META = {'id': ID, 'name': '大福里延庆路29弄3号院门与露台', 'address':'上海市徐汇区延庆路29弄3号',
        'heritage_group': '5D059', 'photographer': 'Livelikerw', 'photo_date': '2016-02-06',
        'photo_reference': 'https://commons.wikimedia.org/wiki/File:Dafu_Li_Shanghai.JPG',
        'photo_reference_license': 'CC BY-SA 4.0', 'photos_embedded': False,
        'viewer_page': SLUG + '.html',
        'scope': '3号院门、门牌、蓝衬铁艺露台及绿框窗所在的局部临弄立面。'}

def add_building(builder, lod=False):
    add_no3(builder, lod, {'window_wall_y': WALL_Y})
    add_terrace(builder, lod, FRONT_Y, WALL_Y)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--lod', action='store_true')
    args = parser.parse_args()
    builder = Builder(PALETTE)
    add_building(builder, args.lod)
    print(builder.save(args.output, META)['sha256'])
