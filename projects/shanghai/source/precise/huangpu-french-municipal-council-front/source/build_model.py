"""Package the bounded street front retained at the 1999 Central Plaza development."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from council_front import PALETTE,make_council
from final_preview import finish

ID='huangpu-french-municipal-council-front'
SCOPE='淮海中路375号所列原法公董局在今381号中环广场沿街保留、复原的北面。覆盖两端与中央前出的砖翼、两段连窗、门廊及街面后约8米的局部屋面。'
META={'id':ID,'name':'法公董局旧址（淮海中路保留立面）','status':'original-photo-informed-exterior',
      'scope':SCOPE,'model_scope_zh':SCOPE,'viewer_page':'french-municipal-council.html',
      'estimated':'用三处公共街景、正门照片、三期航片定位。端点有数米不确定度；高度、坡度、饰面和截面构造为外观估计。',
      'coordinate_convention':'Local GLB +X follows the street west-southwest, +Y is up and +Z faces the public road north-northwest. Origin at the central doorway.',
      'source_register':f'source/precise/{ID}/reference-review.json','interiors_modeled':False,
      'copyright':'Original geometry MIT. Renamed plaque lettering subset SIL OFL 1.1. Reference images are linked separately.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,make_council)
    finish()
