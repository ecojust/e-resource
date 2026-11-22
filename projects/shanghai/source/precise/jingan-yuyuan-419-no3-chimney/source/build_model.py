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
from chimney_and_eaves import ID, PALETTE, add_building, texture

scope='Antigng于2018年2月13日从街道拍摄愚园路419弄3号。取外墙上的高矩形烟囱，以及被烟囱中断的两段棕色瓦檐。'
META=dict(id=ID,name='愚园路419弄3号外墙烟囱与瓦檐',scope=scope,model_scope_zh=scope,viewer_page='yuyuan-419-no3-chimney.html',reference_height_m=6.542,all_dimensions_estimated=True,estimated='名录涵盖419弄3至32号以及愚园路411、427号。这里依摄影者题名辨认3号。从街面仅见烟囱正脸、右侧及两道小压顶，未见顶部烟道开口。进深、逐瓦尺寸与室内烟路均没有实测，截段尺度按照片比例估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
