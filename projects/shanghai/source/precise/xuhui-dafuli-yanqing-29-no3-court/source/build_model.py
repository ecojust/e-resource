"""Reconstruct the photographed No. 3 gateway and terrace at Dafu Li."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if (p / 'tools/package_architectural_model.py').is_file())
sys.path.append(str(PROJECT / 'source/precise/hongkou-general-post-office/source/common'))
sys.path.append(str(PROJECT / 'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
from court_finishes import PALETTE as FINISHES, REPEAT_METRES, apply_court_uv, embed_normals
from court_frontage import PALETTE as FRONTAGE, add_frontage
from court_three import PALETTE as GATE, add_no3
from court_terrace import PALETTE as TERRACE, add_terrace

ID = 'xuhui-dafuli-yanqing-29-no3-court'
SLUG = 'dafuli-yanqing-29-no3-court'
PALETTE = {**GATE, **TERRACE, **FRONTAGE, **FINISHES}
FRONT_Y = .65
WALL_Y = 1.359
META = {'id': ID, 'name': '大福里延庆路29弄3号院门与露台', 'address':'上海市徐汇区延庆路29弄3号',
        'heritage_group': '5D059', 'photographer': 'Livelikerw', 'photo_date': '2016-02-06',
        'photo_reference': 'https://commons.wikimedia.org/wiki/File:Dafu_Li_Shanghai.JPG',
        'photo_reference_license': 'CC BY-SA 4.0', 'photos_embedded': False,
        'viewer_page': SLUG + '.html', 'photo_author': 'Livelikerw',
        'photo_source':'https://commons.wikimedia.org/wiki/File:Dafu_Li_Shanghai.JPG',
        'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
        'camera_views':json.loads((HERE/'cameras.json').read_text()),
        'geometry_license':'MIT except for the traced plate numeral, CC BY-SA 4.0',
        'texture_license':'MIT', 'plate_outline_license':'CC BY-SA 4.0',
        'scope': '3号院门、门牌、蓝衬铁艺露台及绿框窗所在的局部临弄立面。'}

class Builder(CrownBuilder):
    def add(self, vertices, faces, material='limestone', label='detail'):
        super().add(vertices, faces, material, label)
        if material in REPEAT_METRES:
            apply_court_uv(self.parts[-1])

    def save(self, path, metadata=None):
        super().save(path, metadata)
        return embed_normals(path)


def add_building(builder, lod=False):
    add_frontage(builder, lod, FRONT_Y, WALL_Y)
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
