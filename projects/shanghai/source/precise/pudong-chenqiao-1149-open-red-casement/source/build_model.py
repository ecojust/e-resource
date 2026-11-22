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
from red_casements import ID, PALETTE, add_building, texture

scope='Dragon在2023年5月21日拍摄陈桥村1149号，原文把东立面与相邻1156号分节。东墙近照显示左扇向外开启，右扇合拢，露出的固定细杆在窗扇后面。两扇红漆木框各有两道细横档，窗洞侧面呈青灰色粗粒表面。'
META=dict(id=ID,name='陈桥村1149号东墙外开红窗与水刷石窗洞',scope=scope,model_scope_zh=scope,viewer_page='chenqiao-1149-open-red-casement.html',reference_height_m=2.26,all_dimensions_estimated=True,estimated='1149号由独立章节、东立面题注与同组市级标牌共同定位。左窗开启角、窗梃和粗粒面的厚度按照片估计，屋内只用暗面表示透过格杆可见的暗部。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
