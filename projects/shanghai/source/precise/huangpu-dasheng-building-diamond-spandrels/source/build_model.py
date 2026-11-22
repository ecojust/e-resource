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
from spandrel import ID, PALETTE, add_building, texture

scope='市房管局登记九江路230号为大生公司大楼。依Livelikerw于2019年7月11日拍摄的同址街景，制作街面相邻两开间的菱纹窗间墙、深色窗框和檐下曲托。'
META=dict(id=ID,name='大生公司大楼菱纹窗间墙与成列木窗',scope=scope,model_scope_zh=scope,viewer_page='dasheng-building-diamond-spandrels.html',reference_height_m=4.715,all_dimensions_estimated=True,estimated='2019年照片页面把该处题作中菲大楼。模型采用市房管局第五批登记名，大楼沿革不由两种题名推定。檐托深度、浮饰截面、窗扇倾角和立面绝对尺度无实测。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
