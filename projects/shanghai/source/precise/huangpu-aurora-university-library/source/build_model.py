"""Build the 1936 Aurora library elevation facing the playing field."""
from pathlib import Path
import argparse
import os
import sys
SRC=Path(__file__).resolve().parent
sys.path.insert(0,str(SRC.parents[3]/'tools'))
from package_architectural_model import build
from library_front import PALETTE,building
ID='huangpu-aurora-university-library'
SCOPE='重庆南路280号，按2020年球场侧照片制作1936年老红楼北偏西立面、13组窗带与原西1楼号。南面全貌、后部房间和225号博物馆分别另列。'
META={'id':ID,'name':'震旦大学图书馆教学大楼（西一号楼）球场侧立面','status':'original-photo-informed-exterior','viewer_page':'aurora-university-library.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':'原地块约59.70米宽；窗间楼层节距4.50米按两组照片拟合，女儿墙、最低窗台及屋面均为估值。','interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json','coordinate_convention':'Positive X runs west-southwest along the field front, +Y inward to the south-southeast, +Z up.','copyright':'Original geometry and materials, MIT. Photographs are external references.'}
if __name__=='__main__':
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['AURORA_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SRC/'blender_preview.py')]
    build(SRC,META,PALETTE,building)
