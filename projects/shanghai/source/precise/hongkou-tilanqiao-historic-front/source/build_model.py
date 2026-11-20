"""Export the documented 2015 street face at the former Ward Road Gaol."""
from pathlib import Path
import sys
SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from street_portal import PALETTE, add_front

ID = 'hongkou-tilanqiao-historic-front'
SCOPE = '按2015年街景重建长阳路147号旧址门楼临街一面，含叠层石门额、凹槽边柱、退台红砖、封闭深色门面和当年直牌。'
META = {'id':ID,'name':'提篮桥旧址长阳路门楼（2015年街面）','status':'original-photo-informed-exterior',
        'viewer_page':'tilanqiao-historic-front.html','scope':SCOPE,'estimated':SCOPE,'model_scope_zh':SCOPE,
        'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
        'coordinate_convention':'Local X increases toward photo-right, positive Y recedes, Z is up. Dimensions are façade estimates.',
        'copyright':'Original geometry and finishes MIT. Noto Serif CJK subset SIL OFL 1.1. Photos serve as external references.'}
if __name__=='__main__':build(SOURCE,META,PALETTE,add_front)
