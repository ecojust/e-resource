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
from balcony_strips import ID, PALETTE, add_building, texture

scope='Dragon于2020年9月20日拍摄下沙街219至223号住宅；一张近照同时拍到了清晰的223号绿牌和二层楼廊。栏面深色横条之间排列着窄长的红褐色饰板，顶部有短卷纹，上段带收尖的细框，下段有两个菱形小饰。'
META=dict(id=ID,name='下沙街223号楼廊竖饰板的长框与菱花',scope=scope,model_scope_zh=scope,viewer_page='xiasha-223-gallery-relief-strips.html',reference_height_m=1.58,all_dimensions_estimated=True,estimated='现场照片所在章节和保护标牌均标219至223号单号，本件取同图可读223号的门前一段。雕饰表面的材料、线脚最细处和板间暗部不能由照片独断；饰板背面和绝对尺度按比例估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
