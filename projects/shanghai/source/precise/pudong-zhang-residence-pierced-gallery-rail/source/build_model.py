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
from gallery_rail import ID, PALETTE, add_building, texture

scope='Fayhoo于2015年4月25日拍摄东林街65弄7号张氏家宅。院照中，二层廊前的深色横栏夹有一列窄长红色透花栏板。本件取其中四格，用成对卷线、纤细竖条和中央的突起花结表现栏内的空隙。'
META=dict(id=ID,name='三林塘张氏宅二层廊栏的连续红色透花栏板',scope=scope,model_scope_zh=scope,viewer_page='zhang-residence-pierced-gallery-rail.html',reference_height_m=1.46,all_dimensions_estimated=True,estimated='东林街65弄7号的院内照片能确认花栏的位置和重复形状。细线在低分辨率处有遮合，截面、表面材质和绝对尺度均为近似；墙后房间和全院平面未测绘。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
