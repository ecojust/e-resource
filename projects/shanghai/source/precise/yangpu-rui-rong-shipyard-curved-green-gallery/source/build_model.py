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
from curved_gallery import ID, PALETTE, add_building, texture

scope='杨树浦路640号临街建筑的圆转角上，两层外廊各有连续绿铁栏。取圆角上的数扇窄窗、上下阳台板、交叠菱格和下垂弧杆。'
META=dict(id=ID,name='瑞瑢船厂旧址转角双层绿铁栏外廊',scope=scope,model_scope_zh=scope,viewer_page='rui-rong-shipyard-curved-green-gallery.html',reference_height_m=3.46,all_dimensions_estimated=True,estimated='两层栏杆按2015年照片在街角处可读的重复单元重建。曲率、栏杆背面和构件实际厚度为比例估计，未将此立面扩展至其余船厂用地。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
