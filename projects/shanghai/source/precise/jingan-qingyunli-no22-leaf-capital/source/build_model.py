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
from gate_capital import ID, PALETTE, add_building, texture

scope='取襄阳北路22弄入口左侧石柱的上部。高参88于2023年8月5日发表的正面和斜面照片同时显示凹槽柱身、叶饰柱头、方块上的凸圆盘与上方石檐，图中可读22弄门牌。'
META=dict(id=ID,name='青云里襄阳北路22弄入口叶饰石柱头与圆盘',scope=scope,model_scope_zh=scope,viewer_page='qingyunli-no22-leaf-capital.html',reference_height_m=2.493,all_dimensions_estimated=True,estimated='两张照片均为门外视角，叶纹在石面上风化，纹的根数和石材成分未经检测。背面、门内和44弄另一个出入口未进模型。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
