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
from tower import ID, PALETTE, add_building, texture

scope='按Fayhoo于2014年11月29日拍摄并题为广东银行、宁波路52号的现场照片，取转角塔顶层三扇切肩钢窗、窗顶浅色楔块及三级抬起的冠顶。'
META=dict(id=ID,name='广东银行转角塔三面切肩钢窗',scope=scope,model_scope_zh=scope,viewer_page='guangdong-bank-three-faceted-windows.html',reference_height_m=6.36,all_dimensions_estimated=True,estimated='三面的折角、窗进深与顶层后侧缺少现场量测。画面中的空调、缆线及后加招牌不在此段建筑构件范围内。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
