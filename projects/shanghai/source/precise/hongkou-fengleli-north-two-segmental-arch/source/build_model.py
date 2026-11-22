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
from branch_arch import ID, PALETTE, add_building, texture

scope='四川北路1999弄丰乐里的一条支弄口，在祥子g的2016年图文中标明“丰乐里北贰”。本件取低弧红砖券及两侧起拱段，正中有浅色凸缘、内面下凹的券心石。'
META=dict(id=ID,name='丰乐里北贰支弄红砖券与浅色券心石',scope=scope,model_scope_zh=scope,viewer_page='fengleli-north-two-segmental-arch.html',reference_height_m=2.12,all_dimensions_estimated=True,estimated='比例按该文题注的单张正面照片估计，无测绘的绝对高度与墙厚。未辨清的门额文字不在截取范围内。照片记录2016年或以前的外观。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
