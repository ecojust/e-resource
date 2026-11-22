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
from faceted_quoined_bay import ID, PALETTE, add_building, texture

scope='市表登记此住宅在航头镇下沙街西段，2020年9月20日Dragon实拍的上海市优秀历史建筑公布牌标下沙街454号，牌文描述南立面西侧为六边形凸窗、墙面由青砖砌成且转角饰砖砌仿石。院内正照可见凸出的西侧窗面及其右方内凹入口、二层露台。本件截取凸窗上层照片能辨明的三面，包括灰砖、交错角块、窗台及红褐木扇。'
META=dict(id=ID,name='下沙街西段院内住宅南面折角凸窗与仿石隅饰',scope=scope,model_scope_zh=scope,viewer_page='xiasha-454-courtyard-faceted-bay.html',reference_height_m=2.8,all_dimensions_estimated=True,estimated='院内另有航头刘氏宅区级保护牌，作者从巷口回拍同院。挂牌和两组视角共同指向院内主体，街门、其他附房及附近门牌的地籍关系未据此划分。壁厚、转折角、绝对尺寸和背面依照片比例估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
