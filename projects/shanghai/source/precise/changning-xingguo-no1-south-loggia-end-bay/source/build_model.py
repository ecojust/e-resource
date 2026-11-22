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
from end_loggia import ID, PALETTE, add_building, texture

scope='长宁区融媒体中心刊出的近照在图下标出1号楼。模型截取南面图左端的一个敞廊开间，包含两根浅色圆柱、柱间瓶栏、转角侧券、出挑檐和带接缝的浅绿色坡顶。'
META=dict(id=ID,name='兴国宾馆一号楼南立面端部双柱敞廊',scope=scope,model_scope_zh=scope,viewer_page='xingguo-no1-south-loggia-end-bay.html',reference_height_m=5.25,all_dimensions_estimated=True,estimated='市名录以华山路1245号登记整个兴国宾馆，文内分别指认1号、2号和6号楼。瓶栏局部受树枝及柱础遮挡，完整瓶数、柱头小纹饰、屋面实际材质、廊深与绝对尺寸按照片近似。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
