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
from applied_ribbons import ID, PALETTE, add_building, texture

scope='市表5A059登记思南路48号住宅。取Antigng署名的2018年7月30日院照中，上部窗间两行白色曲纹与细竖条。'
META=dict(id=ID,name='思南路48号住宅院侧曲纹窗间与白色贴条',scope=scope,model_scope_zh=scope,viewer_page='sinan-48-courtyard-curved-bands.html',reference_height_m=3.78,all_dimensions_estimated=True,estimated='白色贴条之后可见赭黄色粗墙。绝对尺寸、木材或抹灰配方、旧漆色及窗内布局缺少测绘；从同相原图取各片轮廓。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
