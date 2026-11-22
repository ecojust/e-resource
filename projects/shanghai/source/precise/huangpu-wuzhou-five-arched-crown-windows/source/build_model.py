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
from crown import ID, PALETTE, add_building, texture

scope='按Fayhoo于2015年4月4日拍摄的河南中路220号正面，制作中央高塔最上段的五扇圆头窗、下方第二排方窗与连续上升的轮廓。'
META=dict(id=ID,name='五洲大楼顶层五联券窗与阶梯式冠顶',scope=scope,model_scope_zh=scope,viewer_page='wuzhou-five-arched-crown-windows.html',reference_height_m=6.91,all_dimensions_estimated=True,estimated='窗距、拱高、饰带厚度按照片相对关系估算，塔冠后侧及上方细杆不在本次范围。缺少把局部准确放入城市底图的实测位置。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
