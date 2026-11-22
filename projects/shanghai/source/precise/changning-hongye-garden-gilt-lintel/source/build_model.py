"""Build the photographed Yuecun stone pier, its plaques and its weathering cap."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools'for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from gatehead import add_building,PALETTE
ID='changning-hongye-garden-gilt-lintel'
name='宏业花园1088弄门额与砖柱柱头'
scope='依署名街照表现愚园路1088弄入口的四字金色横额、上下水泥叠涩和两侧砖柱上段。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='hongye-garden-gilt-lintel.html',reference_height_m=1.90,estimated='截取上部，尺度与出挑深度按照片推定。字体取可重现的近似字形。',copyright='Original model and generated materials; glyph outlines derived from Noto Serif CJK SC under SIL OFL 1.1.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
