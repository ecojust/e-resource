"""Package original geometry for the Paramount's two street fronts and beacon."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from ballroom import PALETTE,add_ballroom
ID='jingan-paramount-ballroom'
SCOPE='愚园路218号的百乐门历史建筑，含弧形东入口、两块竖排PARAMOUNT字牌、圆柱灯塔、临愚园路与万航渡路的短翼和宽翼厅顶。'
META=dict(id=ID,name='百乐门舞厅（愚园路218号圆角立面与灯塔）',viewer_page='paramount-ballroom.html',status='original-photo-and-footprint-informed-exterior',scope=SCOPE,model_scope_zh=SCOPE,
          estimated='地面按实名建筑857与道路位置。圆形灯塔、檐口、屋面坡度及门窗尺寸按2025年发布的图像与早期街景比例估算。',
          coordinate_convention='glTF +X north, +Y up, +Z east toward the road junction.',interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',
          copyright='Original geometry and lettering MIT. Reference imagery is not embedded.')
if __name__=='__main__':build(SOURCE,META,PALETTE,add_ballroom)
