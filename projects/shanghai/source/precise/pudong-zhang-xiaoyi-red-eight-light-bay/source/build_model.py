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
from oriel_sashes import ID, PALETTE, add_building, texture

scope='2015年1月10日的署名正照显示，新场大街283号张小乙宅门廊上方设浅凸窗。临街一面有四组双扇红框窗，每一扇由三道细横梃分为四格；窗下竖木板表面露出深浅不一的旧红色。'
META=dict(id=ID,name='张小乙宅临街浅凸窗的八扇红框四格窗',scope=scope,model_scope_zh=scope,viewer_page='zhang-xiaoyi-red-eight-light-bay.html',reference_height_m=2.16,all_dimensions_estimated=True,estimated='照片正对凸窗，窗带的折线、红框分扇和横梃可辨。侧面的转角深度、铰链直径、旧漆状况及绝对尺寸按此估计；不外推上部栏杆、室内及邻接房屋。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
