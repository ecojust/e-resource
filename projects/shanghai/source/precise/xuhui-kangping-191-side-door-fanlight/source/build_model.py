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
from arched_transom import ID, PALETTE, add_building, texture

scope='高参88在康平路187、189、191号的逐幢图录中，把一张拱形深褐木门的照片题作“康平路191号边门”。其扇窗有五根放射梃和两道同心弧梃，门框上缘在中央轻微隆起。'
META=dict(id=ID,name='康平路191号边门的双道弧梃与五辐扇窗',scope=scope,model_scope_zh=scope,viewer_page='kangping-191-side-door-fanlight.html',reference_height_m=1.322,all_dimensions_estimated=True,estimated='市表5D094并列三个单号，本件按照片题注仅归191号边门。射线夹角、白色灰塑凸出深度和窗框进深依照片估计，下部木门与门内空间不在所取局部中。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
