"""Build the courtyard colonnade and split-level entrance at 1634 Huaihai Middle Road."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from courtyard import PALETTE, add_building

ID = 'xuhui-huaihai-road-1634-residence'
SCOPE = '淮海中路1634号院内可见的方柱转角围廊、花铁栏杆、高台阶双扇门与相邻低门。此段屋坡及台基依院照与航空影像估算，北侧和西侧其余住宅保留市底图外形。'
META = {'id':ID,'name':'淮海中路1634号花园住宅（院内柱廊与错层入口）','status':'photo-informed-courtyard-exterior',
        'viewer_page':'huaihai-road-1634-residence.html','scope':SCOPE,'model_scope_zh':SCOPE,
        'estimated':'台阶、柱距、檐高和瓦坡按两张可核实的院照估算。','source_register':'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled':False,'coordinate_convention':'Metres, Z up. +X points east-northeast, +Y north-northwest, placement heading -20 degrees.',
        'copyright':'Original architectural mesh under MIT. External photographs and aerial images used only as references.'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['HUAIHAI_1634_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
