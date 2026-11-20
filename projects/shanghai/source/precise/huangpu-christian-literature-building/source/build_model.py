"""Package the historical Huqiu Road frontage of the Christian Literature Society."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from huqiu_front import PALETTE,add_west
ID='huangpu-christian-literature-building'
SCOPE='广学大楼虎丘路128号临街西立面和可见的浅侧返，依据2010年代以前的档案照片、2015年正照以及2022年修缮报道的实拍。圆明园路东侧真光大楼为独立建筑。'
META={'id':ID,'name':'广学大楼虎丘路西立面','status':'original-photo-informed-exterior','viewer_page':'christian-literature.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json','coordinate_convention':'Local X runs south along the Huqiu Road front, +Y east into the west building, +Z up.','copyright':'Original geometry and procedural materials MIT; sign font subset SIL OFL 1.1. No photo textures.'}
if __name__=='__main__':build(SOURCE,META,PALETTE,add_west)
