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
from keyed_school_window import ID, PALETTE, add_building, texture

scope='按Fayhoo 2015年12月26日所摄愚园路404号市西中学2号楼，仅重建院内正面一组深色双扇窗、窄石中梃和左右各三块伸入灰石面层的窗套。'
META=dict(id=ID,name='市西中学2号楼双扇窗与咬接石窗套',scope=scope,model_scope_zh=scope,viewer_page='shixi-school-keyed-paired-window.html',reference_height_m=2.69,all_dimensions_estimated=True,estimated='照片可确定石套与外墙的轮廓、投影和上下分格；窗洞绝对尺寸、窗扇材质和石套背后的墙体厚度未测。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
