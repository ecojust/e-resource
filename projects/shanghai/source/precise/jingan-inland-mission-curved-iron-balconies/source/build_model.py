import os
from pathlib import Path
import sys
source = Path(__file__).resolve().parent
roots = list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):
    roots.insert(0, Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools = next(parent/'tools' for parent in roots if (parent/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(tools))
from package_architectural_model import build
from curved_balconies import ID, PALETTE, add_building, texture

scope='依据Fayhoo于2016年2月12日所摄并标为北京西路1400弄24号五层北楼的照片，选连续三开间阳台中央一间最上两层。两层弧形出挑的阳台、铁栏和背后的两对窗均可见。'
META=dict(id=ID,name='基督教内地会旧址北楼弧形挑台与交叉圆环铁栏',scope=scope,model_scope_zh=scope,viewer_page='inland-mission-curved-iron-balconies.html',reference_height_m=5.41,all_dimensions_estimated=True,estimated='市表同时登记园内多楼，所选北楼未换算为现有院内楼号。栏下地坪、横檐向外出挑深度和侧接长度按单张斜照估计。中央左右的细部铁花仅可辨大致卷曲形态。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
