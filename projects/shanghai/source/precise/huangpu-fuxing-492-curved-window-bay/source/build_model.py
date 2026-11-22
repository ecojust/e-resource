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
from curved_bay import ID, PALETTE, add_building, texture

scope='取市第五批名录复兴中路492号住宅院面的一层浅弧窗湾。Antigng于2017年8月2日拍摄的正面照片可辨两根浅色圆柱，中间较宽的窗和两侧窄窗下方分别留出短段瓶形栏杆。'
META=dict(id=ID,name='复兴中路492号住宅浅弧窗湾与瓶形栏杆',scope=scope,model_scope_zh=scope,viewer_page='fuxing-492-curved-window-bay.html',reference_height_m=4.53,all_dimensions_estimated=True,estimated='窗湾截取自院中较高的两层开窗中的下层。照片没有给出平面尺寸，栏板投影、窗深和柱径按可见比例估计。左侧树叶遮挡的线脚在模型中止于可见边界。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
