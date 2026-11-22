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
from chevron_frieze import ID, PALETTE, add_building, texture

scope='取襄阳南路254号公寓的屋顶局部。两根较高的墙墩夹着一列重复下折纹样，饰带下为密布短托的深暗水平缝。墙墩石帽以下各有三条长短不同的垂饰。'
META=dict(id=ID,name='襄阳公寓顶层折纹饰带与悬垂边柱',scope=scope,model_scope_zh=scope,viewer_page='xiangyang-apartments-chevron-frieze.html',reference_height_m=1.44,all_dimensions_estimated=True,estimated='2018年原照从街面向上仰拍，树冠和外搭雨篷遮挡下部。宽高、折条截面和支承进深均依可见比例估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
