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
from garden_window import ID, PALETTE, add_building, texture

scope='按Antigng于2018年7月30日自庭院拍摄的皋兰路28号住宅照片，取上层一樘棕色分格窗、浅色颗粒粗面墙、挑窗台和上方暗色檐缘。'
META=dict(id=ID,name='皋兰路28号住宅庭院侧石粒墙与分格木窗',scope=scope,model_scope_zh=scope,viewer_page='gaolan-28-aggregate-casement.html',reference_height_m=2.966,all_dimensions_estimated=True,estimated='树枝遮去右扇的大部分分格。右扇借左扇证实的构造补齐；窗扇启闭方式、石粒种类、两侧庭院墙深度和绝对高程未实测。模型仅呈现院侧窗间一段。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
