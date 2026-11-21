"""Build the editable Kinnear Apartments steel-window bay."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from street_window import PALETTE,add_building,texture
ID='changning-kinnear-apartments-steel-window-bay'
name='开纳公寓钢窗与砖垛'
scope='2014年署名街景中一处上层窗带的通长上亮、四扇细钢窗格、左侧砖垛和叠线窗台。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='kinnear-apartments-steel-window-bay.html',reference_height_m=2.34,estimated='尺寸按照片比例估算。',copyright='Original geometry and plaster texture.')
if __name__=='__main__':
    texture(source/'roughcast.png')
    build(source,META,PALETTE,add_building)
