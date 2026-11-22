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
from relief_panels import ID, PALETTE, add_building, texture

scope='市表5A039登记四川中路330号为Bank of chosen／上海市直接税局。按Livelikerw在2016年2月18日拍摄的临街面，截取两个相邻窗列及其间两段深色浮饰板。'
META=dict(id=ID,name='四川中路330号深色浮饰窗间板与通高窗列',scope=scope,model_scope_zh=scope,viewer_page='sichuan-330-relief-spandrel.html',reference_height_m=5.52,all_dimensions_estimated=True,estimated='浮饰以实照可分辨的外框、双心饰、卷枝起伏表达。面板金属种类、原面漆和每片细纹题材没有材料检验；现场店招、线路和树枝另行区分。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
