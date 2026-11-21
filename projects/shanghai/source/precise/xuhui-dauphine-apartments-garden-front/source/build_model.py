"""Build the photographed south front of the Dauphine Apartments."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from garden_front import PALETTE,make_front

ID='xuhui-dauphine-apartments-garden-front'
SCOPE='建国西路394号道斐南公寓南面九层立面，含中央凸窗、弧形入口雨棚、圆窗与挑出阳台。'
META=dict(id=ID,name='道斐南公寓南向花园立面',status='original-photo-informed-exterior',
          scope=SCOPE,model_scope_zh=SCOPE,viewer_page='dauphine-apartments.html',
          estimated='投影长度与层高按天平街道原图、2014年实名正面照和2020年街景估计。阳台与中央凸窗按正面复原。背街面及公寓内部留待另查。',
          coordinate_convention='Local X runs east along the south facade. Local Y points inward and glTF +Y points up.',
          source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,
          copyright='Original MIT geometry. Third-party photos are not embedded.')
if __name__=='__main__':build(SOURCE,META,PALETTE,make_front)
