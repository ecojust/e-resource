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
from garden_gable import ID, PALETTE, add_building, texture

scope='市表5A055登记复兴中路563号住宅。取Antigng于2018年7月30日署名拍摄的旧住宅，范围从左侧坡檐至中央双扇窗、窗下浅色百叶罩及其金属托架。'
META=dict(id=ID,name='复兴中路563号住宅山墙木格与悬挑百叶罩',scope=scope,model_scope_zh=scope,viewer_page='fuxing-563-gable-timberwork.html',reference_height_m=4.65,all_dimensions_estimated=True,estimated='木构件部分被树枝挡住，取照片能辨认的坡向、横竖分格和一段弧形支撑。绝对尺度、截面和托架进深为估算。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
