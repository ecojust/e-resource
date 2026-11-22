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
from saddle_wall import ID, PALETTE, add_building, texture

scope='Fayhoo于2015年1月27日上传的新场叶氏花行院照，图说为“叶氏花行（叶瑞生） 洪西街120号”。院内门旁绿牌可读120，后方白墙的脊瓦先升高卷起，再跌落为深凹弧，临院一端压有短小的山尖状线脚。'
META=dict(id=ID,name='新场叶氏花行120号院内凹曲山墙与叠瓦压顶',scope=scope,model_scope_zh=scope,viewer_page='ye-cotton-shop-saddle-gable.html',reference_height_m=1.98,all_dimensions_estimated=True,estimated='5W007覆盖洪西街114至126号双号并列新奉公路105号，本件仅按题注和同图门牌落在120号院。照片上传日期可核，确切拍摄日未见记录。山墙进深、背侧与瓦端伸出量按斜视估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
