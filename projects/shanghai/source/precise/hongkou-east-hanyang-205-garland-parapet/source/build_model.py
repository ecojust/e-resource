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
from swag import ID, PALETTE, add_building, texture

scope='Fayhoo的2016年2月6日庭院正照显示，花园住宅的左右两翼各有一块屋顶饰面。本件取画面右翼一块，复原向中央下垂的叶花、左端短叶坠、两头的卷带和直凹线边框。'
META=dict(id=ID,name='东汉阳路205号花园住宅右翼女儿墙花环垂饰',scope=scope,model_scope_zh=scope,viewer_page='east-hanyang-205-garland-parapet.html',reference_height_m=1.185,all_dimensions_estimated=True,estimated='未实测屋顶饰板的绝对尺度。枝叶的朝向按照片可辨的起伏排列，果花数量、背面厚度和被线缆短暂遮住的边缘为近似。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
