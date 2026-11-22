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
from curved_green_roof import ID, PALETTE, add_building, texture

scope='按Windmemories于2026年2月9日署名拍摄的威海路590弄77号现貌，取弧形凸出部最上端绿色圆顶、短顶管、横向搭接线、竖肋和石饰鼓座的可见前半部。'
META=dict(id=ID,name='张园威海路590弄77号绿肋圆顶与石饰鼓座',scope=scope,model_scope_zh=scope,viewer_page='zhang-garden-no77-ribbed-cupola.html',reference_height_m=2.69,all_dimensions_estimated=True,estimated='视图未露出圆顶后沿、烟囱后的肋和石座背面。直径、进深、竖肋与内凹面板在背面的完整数量缺测，仅呈现正面研究片段。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
