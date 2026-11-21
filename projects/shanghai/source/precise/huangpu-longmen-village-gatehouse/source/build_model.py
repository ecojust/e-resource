"""Build the public street entrance to Longmen Village at Lane 133."""
import argparse
import os
import sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from gatehouse import PALETTE,add_building
ID='huangpu-longmen-village-gatehouse'
SCOPE='尚文路133弄总弄口过街楼的贯通拱洞、石质左右门柱、龍門邨匾额、红砖嵌带、红木双扇、上部百叶、1935纪年和两重起翘灰瓦檐。以修缮后街面形态制作。'
META={'id':ID,'name':'龙门邨尚文路总弄过街楼','viewer_page':'longmen-village-gatehouse.html',
      'status':'original-photo-informed-gatehouse','model_scope_zh':SCOPE,'scope':SCOPE,
      'estimated':'洞宽、进深、上部尺度和背面按多张街巷照片及地图估算。门匾用通行字形近似，原题款及印章未辨。','interiors_modeled':False,
      'reference_height_m':15.35,'source_register':'source/precise/'+ID+'/reference-review.json',
      'coordinate_convention':'Metres, Z up. X follows the road east. Y points north into the public lane.',
      'copyright':'Original geometry and granite texture, MIT. Renamed sign lettering subset, SIL OFL 1.1. Photographs served as visual references.'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    opts,rest=parser.parse_known_args()
    os.environ['LONGMEN_GATE_BLENDER']=opts.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
