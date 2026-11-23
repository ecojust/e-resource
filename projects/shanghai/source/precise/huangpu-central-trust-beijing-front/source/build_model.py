"""Build the Beijing Road elevation, lightwell and banking hall ceiling."""
import argparse
import json
import os
import sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from beijing_front import add_front,MATERIALS,HEIGHT
from art_glass import GLASS_MATERIALS
from banking_hall import add_front_wing,HALL_MATERIALS
from trust_portal import add_portal,PORTAL_MATERIALS,PORTAL_CUT
ID='huangpu-central-trust-beijing-front'
SCOPE='北京东路三开间正面、原五层石面与其上两层街面、柱廊、前楼天井及银行厅修复后的彩绘天棚。'
META={'id':ID,'name':'中一信托大楼北京东路正立面与银行大厅彩绘天棚','viewer_page':'central-trust-beijing-front.html',
      'status':'restored-front-elevation-lightwell-and-skylight','scope':SCOPE,'model_scope_zh':SCOPE,
      'reference_height_m':HEIGHT,'interiors_modeled':'仅含天棚及其下方可辨的展厅一段。',
      'estimated':'街宽按OSM登记，窗轴、各层高度由实照估计，天棚长度和宽度由二层图套合。前楼屋面与内侧墙面含推定。',
      'coordinate_convention':'Metres. X follows Beijing Road east from the southwest frontage corner. Y points inward and Z up.',
      'source_register':'source/precise/'+ID+'/reference-review.json',
      'copyright':'Original geometry, MIT. Font subset is separately licensed under SIL OFL 1.1. Reference photographs remain external.'}
PALETTE={**MATERIALS,**HALL_MATERIALS,**GLASS_MATERIALS,**PORTAL_MATERIALS}

def add_building(builder,lod):
    plan=json.loads((SOURCE/'plan-registration.json').read_text())
    add_front(builder,lod,plan['south_width_m'],add_portal,PORTAL_CUT['width'],PORTAL_CUT['height'])
    add_front_wing(builder,plan,lod)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['CENTRAL_TRUST_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
