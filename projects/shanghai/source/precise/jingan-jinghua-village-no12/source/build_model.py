"""Build the street-facing southern elevation of the documented No. 12 home."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from dwelling import PALETTE,add_front

ID='jingan-jinghua-village-no12'
SCOPE='巨鹿路820弄景华新邨12号弄内南向三层单户门面，含木门、上亮、双灯、12号绿牌、窗框、花坛、分户竖墙与檐板。'
META=dict(id=ID,name='景华新邨12号弄内门面',viewer_page='jinghua-village-no12.html',
          scope=SCOPE,model_scope_zh=SCOPE,status='documented-lane-house-frontage',
          estimated='2020年12号近照确定入口与门牌，2026年实地采访补充楼层与花坛。宽度按三期屋顶分户估计，高度、上层窗格与色调参考同排建筑。',
          coordinate_convention='GLB +Z faces into the lane, +X runs approximately east-northeast along the row, and +Y is up.',
          interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',
          copyright='Original mesh MIT. Reference photographs retain their source rights. The address font subset is SIL OFL 1.1.')
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_front)
