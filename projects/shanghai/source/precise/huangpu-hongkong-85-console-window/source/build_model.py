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
from console_window import ID, PALETTE, add_building, texture

scope='香港路85号红砖平立面下排三处相似高窗中，取中间一窗。Antigng在2017年8月31日拍下了左右两个卷头石托、上方出挑的线脚，以及下格向外打开的深色钢窗。'
META=dict(id=ID,name='香港路85号卷首石托窗楣与外开钢窗',scope=scope,model_scope_zh=scope,viewer_page='hongkong-85-console-window.html',reference_height_m=4.82,all_dimensions_estimated=True,estimated='记录来源按门牌区分。2015年规划局名录为AlgarBuilding，市房管局第五批5A075在同号登记“美国陆海军青年会／海青大楼”。1927年建筑师学会会刊记Algar Building在Hong Kong Road，1936年广告写当时60号。旧60与今85的换号没有在现有资料中得到核实。四川中路630号的另幅实照和本窗分开登记，现无两正面结构相连的测绘依据。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
