"""Build the double-height timber veranda photographed at 630 Huashan Road."""
from pathlib import Path
import sys
import os
from argparse import ArgumentParser
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from veranda import PALETTE, add_building
ID='jingan-xiong-foxi-building-corner-veranda'
NAME='熊佛西楼东南转角双层木围廊'
SCOPE='华山路630号院内熊佛西楼南侧东两开间和东侧第一开间，包括双层木柱斜撑、铁栏、水平百叶、内侧青红砖墙和通风基座。'
META={
    'id':ID,'name':NAME,'viewer_page':'xiong-foxi-corner-veranda.html',
    'status':'photo-informed-xiong-foxi-corner-veranda','model_scope_zh':SCOPE,'scope':SCOPE,
    'estimated':'以2014年5月与8月两张署名实照和三期屋顶影像定位。柱距由东南斜照与OSM足印标定，内墙退深及竖向为估算。',
    'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
    'coordinate_convention':'Metres, Z up. The origin is the SE post at OSM vertex 1. Positive X is east along the long gallery and positive Y north along the return. Datum is the paving.',
    'copyright':'Original geometry under MIT. Documentary images are credited and not embedded.'
}
if __name__=='__main__':
    parser=ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['XIONG_FOXI_324_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
