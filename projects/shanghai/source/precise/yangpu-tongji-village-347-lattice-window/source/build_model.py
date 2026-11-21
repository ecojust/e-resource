"""Build the editable No.347 high window and four open cement panels."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from window_bay import PALETTE,add_building,texture
ID='yangpu-tongji-village-347-lattice-window'
name='同济新村347号高窗与方形花格'
scope='2015年署名照片中的浅色突窗墙、两扇外倾窗扇、四片方形水泥花格及窗上短瓦盖。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='tongji-village-347-lattice-window.html',reference_height_m=3.70,estimated='尺寸按照片比例估算。',copyright='Original geometry and plaster texture.')
if __name__=='__main__':
    texture(source/'plaster.png')
    build(source,META,PALETTE,add_building)
