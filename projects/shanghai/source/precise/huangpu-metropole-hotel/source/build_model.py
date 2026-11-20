"""Export editable and streamed models of the Metropole Hotel corner block."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from hotel import PALETTE,add_hotel

ID='huangpu-metropole-hotel'
SCOPE='江西中路180号东北角主楼，含临圆形路口的五段凹弧、花岗石入口、两条沿街短翼、八层以上各级退台和塔冠。'
META=dict(id=ID,name='都城饭店（江西中路180号转角主楼）',viewer_page='metropole-hotel.html',status='original-photo-and-footprint-informed-exterior',scope=SCOPE,model_scope_zh=SCOPE,
          estimated='地面依据实名地图地块及邻接关系。参考高度约65米，各层、塔冠和侧后露台按照片比例和屋顶影像估计。',
          coordinate_convention='glTF +X southeast along the corner, +Y up, +Z southwest toward the junction.',
          interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',
          copyright='Original geometry MIT. Reference images are not embedded.')
if __name__=='__main__':build(SOURCE,META,PALETTE,add_hotel)
