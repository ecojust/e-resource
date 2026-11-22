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
from gable_lights import ID, PALETTE, add_building, texture

scope='辽阳路51弄的2014年现场照片里，较高的红砖山墙顶端开三扇共用平窗台的阁窗。中窗以半圆收顶，两侧较矮的窄窗为平头，上方两道坡檐收在同一脊点。'
META=dict(id=ID,name='聂家花园高山墙三联窗与拱顶楔石',scope=scope,model_scope_zh=scope,viewer_page='nie-garden-triple-attic-light.html',reference_height_m=2.97,all_dimensions_estimated=True,estimated='模型仅取可辨认的高山墙阁窗。尺寸按正面照片比例估算，角度、窗腔深度与所见砖缝的细小差异不作实测值。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
