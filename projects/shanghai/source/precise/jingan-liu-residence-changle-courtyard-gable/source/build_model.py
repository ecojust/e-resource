"""Build the photographed timbered gable and canted bay in the Changle Road courtyard."""
from pathlib import Path
from argparse import ArgumentParser
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from courtyard_gable import PALETTE, add_gable

ID='jingan-liu-residence-changle-courtyard-gable'
NAME='刘氏花园住宅长乐路庭院露木山墙与折面凸窗'
SCOPE='长乐路784及786号同院右侧庭院山墙。取2015和2018年照片所见的深色露木、阁窗、二层双窗、底层独窗、折面凸窗及其2015年牌匾、石勒脚与短段瓦檐。'
META={'id':ID,'name':NAME,'viewer_page':'liu-residence-changle-courtyard-gable.html',
      'status':'original-photo-informed-liu-courtyard-gable','model_scope_zh':SCOPE,'scope':SCOPE,
      'estimated':'檐尖约12.93米、墙宽约6.22米。柱框、折面进深与屋面短返按照片和航片约束估计。',
      'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
      'coordinate_convention':'Metres, local X northeast along the courtyard front, Y northwest into the main building, Z up. Front wall at Y=0.',
      'copyright':'Original geometry, MIT. Renamed Noto Sans CJK SC subset under SIL OFL 1.1. Documentary photographs are credited separately.'}
if __name__=='__main__':
    parser=ArgumentParser(add_help=False);parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args();os.environ['LIU_COURTYARD_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_gable)
