"""Build the 2014 public street facade, terraces and corner pavilion."""
from pathlib import Path
import argparse
import os
import sys
SRC=Path(__file__).resolve().parent
sys.path.insert(0,str(SRC.parents[3]/'tools'))
from package_architectural_model import build
from waterfront_office import PALETTE,building
ID='hongkou-east-daming-road-378'
SCOPE='东大名路378号历史红砖办公楼面街七开间、两层退台、西侧短返及翘檐塔亭，参照2014年1月27日街照。内院、独立门房、后部及同门牌30层总部另列。'
META={'id':ID,'name':'东大名路378号红砖办公楼街面与塔亭','status':'original-photo-informed-exterior','viewer_page':'east-daming-378.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':'街面约27.8米，标高、塔亭位置、退台和石饰均为估值。','interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json','coordinate_convention':'Local +X towards the west side of the street facade. Positive Y is inward, positive Z is up.','copyright':'Original geometry and materials, MIT. Photographs are external references.'}
if __name__=='__main__':
    launch=argparse.ArgumentParser(add_help=False)
    launch.add_argument('--blender',default='blender')
    options,remaining=launch.parse_known_args()
    os.environ['DAMING_MODEL_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--blender',str(SRC/'blender_preview.py')]
    build(SRC,META,PALETTE,building)
