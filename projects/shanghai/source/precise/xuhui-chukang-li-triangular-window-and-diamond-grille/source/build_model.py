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
from pediment_grille import ID, PALETTE, add_building, texture

scope='2017年8月19日Antigng拍摄的储康里弄内原照，左侧红砖墙近处的一扇窗有三角形石面窗楣，窗前灰色铁栏的两条横带之间排列同心圆和一对交叠菱形。本作截取窗头、格窗和这一段铁栏。'
META=dict(id=ID,name='储康里红砖墙三角窗楣与双菱铁栏',scope=scope,model_scope_zh=scope,viewer_page='chukang-li-triangular-window-and-diamond-grille.html',reference_height_m=2.177,all_dimensions_estimated=True,estimated='市表5D062记长乐路401弄。照片中另有一块8号牌属于右侧另一栋，本作左窗不附户号。原始门窗用途、翻修年份、墙厚和铁栏前后间距均未见独立测量。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
