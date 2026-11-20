"""Build the numbered gate of the No. 25 Jing'an Villa courtyard."""
from pathlib import Path
import argparse
import os
import sys

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from gate_geometry import PALETTE,add_building

IDENT='jingan-villa-no25'
SCOPE='南京西路1025弄25号沿支弄的红砖院门与相邻的一段本户院墙。按2013年现场照片重建黑色双扇铁门、菱格、气窗、红砖门垛、层叠压顶、灰色勒脚与25号绿牌。门高与砖缝按实物比例估算。住宅后部、邻户及其余里弄留作后续。'
META={'id':IDENT,'name':'静安别墅25号院门与弄面院墙','viewer_page':'jingan-villa-no25.html','status':'original-photo-informed-exterior','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'source_register':'source/precise/'+IDENT+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Metres, Z up. +X runs northeast along the lane toward No. 27 and +Y points northwest into the courtyard. The photographed face is -Y.','copyright':'Original model geometry under MIT. No photographic textures are embedded.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    args,remaining=parser.parse_known_args()
    os.environ['JINGAN_NO25_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_building)
