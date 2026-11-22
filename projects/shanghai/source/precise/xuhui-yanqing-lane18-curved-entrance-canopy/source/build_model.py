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
from curved_canopy import ID, PALETTE, add_building, texture

scope='2018年2月7日Antigng的署名照片拍到延庆路18弄10号住宅的入口，灰色平雨篷从门上挑出，两边各有一道曲托。曲线沿下缘从门侧上翻，近端的侧面可辨圆饰。'
META=dict(id=ID,name='延庆路18弄10号弧托雨篷与圆形端饰',scope=scope,model_scope_zh=scope,viewer_page='yanqing-lane18-curved-entrance-canopy.html',reference_height_m=2.91,all_dimensions_estimated=True,estimated='原照从门外斜下方拍摄，门心、雨篷上表面和一侧曲托被树木遮挡。侧托轮廓、板厚、门洞进深均按可见关系估计。院内格局与绝对尺寸未有测绘。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
