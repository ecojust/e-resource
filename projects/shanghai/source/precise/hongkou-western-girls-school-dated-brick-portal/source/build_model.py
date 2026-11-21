"""Build the shuttered attic gable of building 3 at 48 Pingjiang Road."""
import os
from pathlib import Path
import sys

source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):
    roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from dated_portal import PALETTE, add_building, texture
ID='hongkou-western-girls-school-dated-brick-portal'
SCOPE='塘沽路390号院内可见的门洞、双色砖券、1893及1894年牌、尖山花两侧饰板和门前石阶。'
META=dict(id=ID,name='工部局西童女子学校双年份砖券门',viewer_page='western-girls-school-dated-portal.html',scope=SCOPE,model_scope_zh=SCOPE,reference_height_m=9.02,estimated='据2014年庭院斜照校正正面，展示高度、后侧墙深及低浮饰作近似处理。',source_register='source/precise/'+ID+'/reference-review.json',copyright='Original geometry and running-bond texture. Date numerals approximate the photographed serif forms.')
if __name__=='__main__':
    texture(source/'charcoal-bond.png')
    build(source,META,PALETTE,add_building)
