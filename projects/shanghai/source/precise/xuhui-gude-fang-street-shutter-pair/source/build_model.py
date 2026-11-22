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
from open_shutters import ID, PALETTE, add_building, texture

scope='Antigng于2017年8月19日拍摄的襄阳北路68至72弄住宅街面上，相邻两扇底层窗打开百叶板，左窗红色叶片间隔以白色横档、外缘为浅色，右窗用褐色细密横叶。两窗均带浅石窗台。'
META=dict(id=ID,name='顾德坊沿街两窗的红白百叶与褐色木叶',scope=scope,model_scope_zh=scope,viewer_page='gude-fang-street-shutter-pair.html',reference_height_m=2.18,all_dimensions_estimated=True,estimated='顾德坊名录还包括66弄及74弄。原照可对到68至72弄名下的这一段街面，不能逐窗分配到具体住户。百叶数量按可见密度估算，背面深度、木叶倾斜角也未作现场测量。采样日期所见涂色没有建造年代记录。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
