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
from upper_window import ID, PALETTE, add_building, texture

scope='Livelikerw于2019年2月23日拍摄的宛平路7号街面，最上层赭色墙面开深色格窗，细浅边框和外挑窗台围住三个并排窗扇。檐下的一列浅色方齿以阴影相隔。'
META=dict(id=ID,name='宛平路7号上层三联格窗与齿饰檐口',scope=scope,model_scope_zh=scope,viewer_page='wanping-7-casement-and-cornice.html',reference_height_m=2.55,all_dimensions_estimated=True,estimated='取原照片右段最上层、一对分缝壁柱之间的单窗。窗扇每组三列中的一列含两小格；框色、抹面色与可见接缝依当日记录。构件高宽与进深为照片比例估计，檐齿只表现所选一段。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
