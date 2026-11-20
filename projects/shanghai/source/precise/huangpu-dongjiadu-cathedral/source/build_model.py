"""Export the historic south front of St Francis Xavier Church, Shanghai."""
from pathlib import Path
import sys
SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from facade import PALETTE,front

ID='huangpu-dongjiadu-cathedral'
SCOPE='以2010及2012年实拍为依据的董家渡天主堂南入口立面，含三门、双龛、钟面、双塔与十字架。主堂其余各面、两侧附楼、学校与院落另列。'
META={'id':ID,'name':'董家渡天主堂南入口立面','status':'original-photo-informed-exterior',
      'viewer_page':'dongjiadu-cathedral.html','scope':SCOPE,'estimated':SCOPE,'model_scope_zh':SCOPE,
      'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
      'coordinate_convention':'Local +X east along south front, +Y north into the church, +Z up. GLB uses Y up.',
      'copyright':'Original geometry and materials MIT. Noto Serif CJK outlines SIL OFL 1.1. No photographs embedded.'}
if __name__=='__main__':build(SOURCE,META,PALETTE,front)
