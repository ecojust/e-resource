"""Build the numbered stone piers and the cambered iron gate at 18 Pingwu Road."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools'for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from street_gate import ID,PALETTE,add_building
name='外国弄堂平武路18号院门分段石柱与弧顶铁门'
scope='以2016年有平武路18号题注的街面照片为依据，制作带绿牌的分段门柱、柱顶雕饰、弧顶铁门及相邻短砖墙。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='pingwu-18-rusticated-gate.html',reference_height_m=2.64,estimated='门柱分段及铁门起拱按照片比例取值，绝对尺度、栏杆直径和遮蔽处的做法约略。',copyright='Original geometry and procedural stone finish.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
