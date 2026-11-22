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
from hip_roof import ID, PALETTE, add_building, texture

scope='Antigng在2017年8月19日拍摄的长乐路327至329号住宅照片中，沿街浅色墙上的两扇钢窗共用一片灰褐色瓦顶。两道浅褐斜脊从顶端向深色檐口张开，檐下露出一排短椽头。'
META=dict(id=ID,name='长乐路327至329号住宅双窗上方的斜脊瓦顶',scope=scope,model_scope_zh=scope,viewer_page='changle-327-329-hipped-window-roof.html',reference_height_m=2.82,all_dimensions_estimated=True,estimated='原照与市表均同时列出327、329号。图内这片瓦顶无法细分到其中一个门牌。两条可见斜脊、檐口、窗扇的比例由照片估测；后半屋面与树木遮住的外墙未纳入取景。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
