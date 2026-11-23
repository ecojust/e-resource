"""Build the photographed central garden loggia of the former Sino-German Hospital."""
from pathlib import Path
import sys
import os
from argparse import ArgumentParser
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from loggia import PALETTE, add_building
ID='huangpu-sino-german-hospital-courtyard-loggia'
NAME='中德医院旧址庭院中央门廊与露台'
SCOPE='延安中路393号旧中德医院朝南庭院中轴一跨，包含铁花双门、石柱与二层栏墙、退进后三樘门、三层露台和花槽。'
META={
    'id':ID,'name':NAME,'viewer_page':'sino-german-hospital-courtyard-loggia.html',
    'status':'photo-informed-sino-german-hospital-courtyard-loggia','model_scope_zh':SCOPE,'scope':SCOPE,
    'estimated':'2017年庭院照片与2021年巨鹿路两实景站确定外部构件。进深、雕饰剖面和窗框厚度按图估算。',
    'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
    'coordinate_convention':'Metres, Z up. The origin is on the garden centreline at the southern OSM footprint edge; +X points east along the elevation, +Y into the hospital, and +Z is relative to the garden threshold.',
    'copyright':'Original geometry under MIT. Documentary images are credited and not embedded.'
}
if __name__=='__main__':
    parser=ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['SINO_GERMAN_327_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
