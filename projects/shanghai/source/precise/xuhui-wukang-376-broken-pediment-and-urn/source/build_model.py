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
from broken_pediment import ID, PALETTE, add_building, texture

scope='市表5D018涵盖武康路374、376号。Antigng的署名照片明确标为376号住宅，院内侧翼门口两段石弧的中央留出缺口，一只瓶形饰件立于平檐正中。这里制作门楣、石瓶、左右托座与上亮窗。'
META=dict(id=ID,name='武康路376号住宅断弧门楣与石瓶',scope=scope,model_scope_zh=scope,viewer_page='wukang-376-broken-pediment-and-urn.html',reference_height_m=1.91,all_dimensions_estimated=True,estimated='同项374号的其他门窗未见于这张原照。石饰各层深度和侧面转折按可见轮廓估算。门口下部被绿植遮挡，模型止于上亮窗下框。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
