"""Rebuild the photographed street elevation, set-back wing and courtyard gate at 337 Changle Road."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if (p / 'tools/package_architectural_model.py').is_file())
sys.path[:0] = [
    str(HERE),
    str(PROJECT / 'source/precise/hongkou-general-post-office/source/common'),
    str(PROJECT / 'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'),
]
from photo_architecture import Builder as GeometryBuilder
from crown_builder import CrownBuilder
import courtyard_gate
import street_finishes
import street_wall

ID = 'xuhui-changle-337-courtyard-gate-and-street-house'
SLUG = 'changle-337-courtyard-gate-and-street-house'
PALETTE = {**street_wall.PALETTE, **courtyard_gate.PALETTE, **street_finishes.PALETTE}
META = {
    'id': ID,
    'name': '长乐坊337号院门与相邻临街窗墙',
    'address': '上海市徐汇区长乐路337号',
    'heritage_id': 'sh-historic-b5-xh-j-099-v',
    'heritage_group': '5D099',
    'source': 'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
    'photo_source': 'https://commons.wikimedia.org/wiki/Special:Redirect/page/61784243',
    'photo_author': 'Antigng, 19 August 2017, Wikimedia Commons, CC BY-SA 4.0',
    'photos_embedded': False,
    'geometry_license': 'CC BY-SA 4.0',
    'texture_license': 'CC BY-SA 4.0',
    'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
    'viewer_page': SLUG + '.html',
    'local_axes': 'X runs along the facade toward the west-southwest, positive Y toward the courtyard, Z upwards. Origin at the centreline of the left upper window, at street level.',
    'scope': '337号双扇院门、绿牌与院墙，相邻两开间街窗、内凹小门及退进窗墙。2017年实照为主，2015/2021年街面影像用于量测。',
}

class Builder(CrownBuilder):
    def add(self, vertices, faces, material='limestone', label='detail'):
        before = len(self.parts)
        GeometryBuilder.add(self, vertices, faces, material, label)
        if len(self.parts) > before and material in street_finishes.SURFACES:
            street_finishes.map_finish(self.parts[-1])

    def save(self, path, metadata=None):
        super().save(path, metadata)
        return street_finishes.embed_normals(path)

def add_building(builder, lod=False):
    street_wall.add_front(builder, lod)
    street_wall.add_rear_wing(builder, lod)
    courtyard_gate.add_courtyard_gate(builder, lod)

if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--lod', action='store_true')
    args = cli.parse_args()
    builder = Builder(PALETTE)
    add_building(builder, args.lod)
    print(builder.save(args.output, META)['sha256'])
