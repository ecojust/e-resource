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
from corner_frieze import ID, PALETTE, add_building, texture

scope='Antigng于2018年2月7日拍摄的延庆路42号住宅照片中，街面浅绿拱口内有米色辐形扇窗。灰蓝饰带从扇窗上方延伸至外墙转角；两面的短横纹列在同一高度。'
META=dict(id=ID,name='延庆路42号住宅扇窗与转角灰饰腰线',scope=scope,model_scope_zh=scope,viewer_page='yanqing-42-fanlight-and-returning-frieze.html',reference_height_m=1.822,all_dimensions_estimated=True,estimated='名录同列42号、52号，现场照片题注明确为42号。本件止于一樘扇窗和它正上方的转角腰线；后续开间、52号和一层实体门板未由此图推定。边缘宽度和灰饰凸出深度为照片比例估算。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
