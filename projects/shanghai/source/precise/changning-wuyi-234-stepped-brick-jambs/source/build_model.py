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
from stepped_window import ID, PALETTE, add_building, texture

scope='2018年2月13日的临街照片中，一扇狭长单窗位于前后两层红瓦坡檐之间。浅色框外两列深红横砖分段向浅色墙面伸出，形成阶梯形窗套。'
META=dict(id=ID,name='武夷路234号住宅竖梳粉墙与阶梯砖窗套',scope=scope,model_scope_zh=scope,viewer_page='wuyi-234-stepped-brick-jambs.html',reference_height_m=2.48,all_dimensions_estimated=True,estimated='照片只显示这扇窗的外表，窗框、压顶和墙厚均按照片比例估算。拍摄时的玻璃及窗框年代未考。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
