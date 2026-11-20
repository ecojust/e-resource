"""Package the first Morris Residence and its courtyard entrance."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from residence import PALETTE, add_residence

ID='huangpu-ruijin-guesthouse-01'
SCOPE='瑞金宾馆1号楼主宅体量及北庭院一侧，含成对塔司干柱、石阳台、两层花园窗、红瓦坡顶和烟囱；2号楼、栋间廊及独立酒店扩建体另有边界。'
META=dict(id=ID,name='瑞金宾馆1号楼（马立斯住宅主楼与庭院立面）',viewer_page='ruijin-guesthouse-01.html',
          status='original-photo-and-site-plan-informed-exterior',scope=SCOPE,model_scope_zh=SCOPE,
          estimated='占地依酒店1:500总平面配准。檐高、屋脊、窗格与柱径按外观估计，后侧仅作体量。',
          coordinate_convention='glTF +X toward west-southwest along the courtyard, +Y up, +Z north-northwest outward.',
          interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',
          copyright='Original geometry MIT. Reference photography and survey artwork are not embedded.')
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_residence)
