"""Build the repaired street entrance and flanking window walls of the original Shanghai YMCA."""
import argparse
import os
import sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from east_front import PALETTE,add_building
ID='huangpu-puguang-ymca-east-entrance'
SCOPE='按2023年修缮后街照建立四川中路599号石门套、木门与钟面、三行英文铭刻、南北各一道商铺券洞、上层六扇窗及砖石断山花。高层加建和其余开间保留底图。'
META={'id':ID,'name':'浦光大楼（上海基督教青年会）四川中路门头与东立面窗墙','viewer_page':'puguang-ymca-east-entrance.html',
      'status':'photo-informed-restored-east-front','model_scope_zh':SCOPE,'scope':SCOPE,'reference_height_m':15.04,
      'estimated':'15.04米为此次细化至砖墙的最高断面，整楼原城楼顶22.4米。依据街墙37.31米及原照扇窗比例估算标高和进深。',
      'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
      'coordinate_convention':'Metres, Z up. Positive X goes north along the street and negative Y faces Sichuan Middle Road.',
      'copyright':'Original geometry and brick texture, MIT. The font subset has separate SIL OFL 1.1 licensing. Reference photos are credited in the source register.'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    opts,rest=parser.parse_known_args()
    os.environ['PUGUANG_FRONT_BLENDER']=opts.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
