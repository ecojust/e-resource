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
from paired_sashes import ID, PALETTE, add_building, texture

scope='依Antigng于2018年1月28日拍摄的校舍，取朝向镜头的两列窗带，包含上下两层双扇深色窗、浅色矩形窗间板、灰墙水平分缝和檐口。'
META=dict(id=ID,name='培明中学双列深色窗与浅色窗间板',scope=scope,model_scope_zh=scope,viewer_page='peiming-school-paired-sash-bands.html',reference_height_m=5.07,all_dimensions_estimated=True,estimated='门前设施遮挡底层。照片只确定这处现貌，窗框材质依表面色泽估计，外墙深度与绝对尺寸未有测绘依据。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
