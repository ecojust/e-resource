"""Build the triple window and foliate shield beside the photographed Mingzhe portico."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools'for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from window_bay import add_building,PALETTE
ID='changning-mingzhe-building-triple-window'
name='明哲楼南面三联长窗与盾形窗饰'
scope='依据2014年刊出的1号楼斜照和一层窗组正面近照，建模三联长窗、浅壁柱、格扇与盾形卷叶花饰。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='mingzhe-building-triple-window.html',reference_height_m=3.4,estimated='绝对长度、雕饰截面和后墙深度按照片比例近似。',copyright='Original geometry and generated materials based on attributed references.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
