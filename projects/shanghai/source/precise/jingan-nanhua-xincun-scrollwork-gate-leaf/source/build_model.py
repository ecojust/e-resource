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
from iron_leaf import ID, PALETTE, add_building, texture

scope='Livelikerw于2016年2月6日从长乐路街侧拍到774弄入口。取靠右侧「南華新邨」题名门墩的黑色铁门上段，重现两格门框、弯顶与透空花铁。'
META=dict(id=ID,name='南华新邨长乐路774弄入口尖矛花铁门',scope=scope,model_scope_zh=scope,viewer_page='nanhua-xincun-scrollwork-gate.html',reference_height_m=2.09,all_dimensions_estimated=True,estimated='照片里铁门斜向街沿、门底又被车遮住，门扇展开后的宽度与弧高为比例估计。卷纹按可辨的重复形制简化。下沿是本项的裁切线。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
