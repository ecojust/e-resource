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
from round_bay import ID, PALETTE, add_building, texture

scope='建国西路365弄支弄照片中的黄色弧墙，凹入的圆首钢窗、下层白色腰线和檐下圆端小齿。2017年署名街照可辨瓦端、三道横窗梃和上部扇形细钢条。'
META=dict(id=ID,name='台拉新村支弄弧墙上的圆首钢窗与白色檐带',scope=scope,model_scope_zh=scope,viewer_page='tailaxincun-curved-bay-and-arched-window.html',reference_height_m=3.035,all_dimensions_estimated=True,estimated='市表记录一组住宅。照片标至支弄，未见这一跨的门牌。墙体曲率、窗深和瓦片进深按照片估算。侧边、底部和后部为局部截面。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
