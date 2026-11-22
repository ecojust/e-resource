"""Build the red-brick corner documented by Changning District's heritage register."""
import os,sys
from pathlib import Path
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from red_corner import ID,PALETTE,add_building
name='愚园路749弄65号花园住宅红砖圆转角'
scope='以长宁区规资局所刊原照制作红砖转角、两道浅色腰线、底层窄窗与上部直角挑檐。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='yuyuan-749-no65-red-brick-corner.html',reference_height_m=10.162,estimated='砖皮节距、带高和窗侧比例依据原照，圆角半径、绝对高度、转角角度与背面厚度按比例推定。',copyright='Original geometry and procedural running-bond texture. The district photograph is cited at its source.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
