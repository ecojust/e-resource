"""Package the two dated street elevations and central crown at the Medhurst Apartments."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from medhurst_front import PALETTE,make_front

ID='jingan-medhurst-apartments'
SCOPE='南京西路934号泰兴大楼的五段折线街面，包括中央十二层高段、五道挑脊和两侧九层带窗翼部。'
META=dict(id=ID,name='泰兴大楼（MEDHURST大楼）南京西路与泰兴路转角',status='original-photo-informed-exterior',
          scope=SCOPE,model_scope_zh=SCOPE,viewer_page='medhurst-apartments.html',
          estimated='层高、短进深、窗扇小格与冠部进深按两张沿街实照和冻结地形估计。后侧以局部剖切面收边，原楼后半部与邻房保留。',
          coordinate_convention='Author +X runs from the Nanjing Road wing toward the Taixing Road wing. +Y points inward and glTF +Y is up.',
          source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,
          copyright='Original MIT geometry; no third-party pictures or logos embedded.')
if __name__=='__main__':build(SOURCE,META,PALETTE,make_front)
