"""Build both geometry levels of the registered Petain Apartments street spandrel."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if 'SHANGHAI_MODEL_TOOLS' in os.environ:roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(root/'tools' for root in roots if (root/'tools/package_architectural_model.py').exists())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from spandrel import add_building,PALETTE,make_texture
ID='xuhui-petain-apartments-scalloped-spandrel'
META=dict(id=ID,name='贝当公寓临街窗下圆珠与弧带浮饰（2013年外观）',viewer_page='petain-apartments-scalloped-spandrel.html',scope='衡山路700号照片左端窗跨。以2013年12月原片描绘窗裙弧带、圆片、出挑窗台和四列窗扇。',model_scope_zh='单一历史窗跨局部，以照片比例表达。',reference_height_m=4.51,estimated='窗裙名义宽2.05米；未取得原建筑详图，厚度按浮饰阴影估计。',source_register='source/precise/'+ID+'/reference-review.json',copyright='Original geometry and procedural roughcast texture. No source photographs embedded.')
if __name__=='__main__':
    make_texture(source/'mineral-grain.png');build(source,META,PALETTE,add_building)
