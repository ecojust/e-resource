"""Build the photographed Yuecun stone pier, its plaques and its weathering cap."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools'for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from gate_pier import add_building,PALETTE
ID='changning-yuecun-lane-480-entrance-pier'
name='月村江苏路480弄双号牌门柱'
scope='依2018年1月署名照所见，复原临弄左侧石门柱、68号铭牌和下方题有66号的蓝牌。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='yuecun-lane-480-entrance-pier.html',reference_height_m=2.58,estimated='门柱高宽与进深按单幅街景的比例估算，柱背采用连续剖面。',copyright='Original geometry and textures based on attributed references.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
