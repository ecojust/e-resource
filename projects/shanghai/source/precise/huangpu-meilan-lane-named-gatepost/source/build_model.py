"""Build the street-facing named pier and document wall in Meilan Lane."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gatepost import PALETTE,add_gatepost
ID='huangpu-meilan-lane-named-gatepost'
NAME='梅兰坊黄陂南路596弄题名门柱与铭牌墙'
SCOPE='黄陂南路596弄正对院口的左侧灰石门柱、三字金色题名、柱座与顶盖及相接南侧门牌、文保牌与告示框墙。右柱亦题名，院门和院内成排住宅另列。'
META=dict(id=ID,name=NAME,viewer_page='meilan-lane-named-gatepost.html',status='photo-informed-meilan-named-street-pier',scope=SCOPE,model_scope_zh=SCOPE,source_register='source/precise/'+ID+'/reference-review.json',interiors_modeled=False,estimated='2020年两个街站配准，平面约±0.55米、高约±0.30米。柱高约3.71米；柱背深度和细部断面依正斜面照片推定。',coordinate_convention='Metres. X runs north-northwest on South Huangpi Road. Y points into the block. The origin is on the face below the gold name.',copyright='Original MIT geometry. Documentary photographs are credited separately; the municipal plaque font subset uses SIL OFL 1.1.')
if __name__=='__main__':
 a=ArgumentParser(add_help=False);a.add_argument('--blender',default='blender');opt,other=a.parse_known_args();os.environ['MEILAN_PIER_BLENDER']=opt.blender
 sys.argv[1:]=[*other,'--blender',str(SOURCE/'blender_preview.py')];build(SOURCE,META,PALETTE,add_gatepost)
