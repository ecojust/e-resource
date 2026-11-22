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
from octagonal_eye import ID, PALETTE, add_building, texture

scope='在2018年冬季的武夷路154号街照中，后排红砖墙有一个平顶、平底的八角形开口，八边沿口均有朝洞口排列的红砖。深色洞面中央留有一根横档，上方檐下是竖砖带。'
META=dict(id=ID,name='武夷路154号住宅山墙八角砖窗与横档',scope=scope,model_scope_zh=scope,viewer_page='wuyi-154-octagonal-brick-light.html',reference_height_m=2.44,all_dimensions_estimated=True,estimated='原拍摄位置低于开口，无法辨认其深处是否另装玻璃或百叶。模型采用暗底表示照片中可辨的深色平面，尺寸及进深是近似值。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
