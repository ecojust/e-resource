"""Package the 1931 Lyceum Theatre entrance, two street wings and auditorium roof."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from lyceum_geometry import PALETTE,add_building

ID='huangpu-lyceum-theatre'
SCOPE='茂名南路57号兰心大戏院，以2012及2019年实照为入口依据。三扇拱窗、三联上窗、石阳台、雨篷、沿街两翼及可从影像辨认的蓝灰拱顶和后台屋面。背墙、设备及标高估计，未复原内饰。'
META={'id':ID,'name':'兰心大戏院（茂名南路57号）','status':'original-photo-informed-exterior','viewer_page':'lyceum-theatre.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Metres, local +X along the street corner front and -Y towards the Maoming and Changle intersection. Map heading 40.60 degrees clockwise.','copyright':'Original geometry MIT. Gilded sign uses a renamed SIL OFL subset. No photographs embedded.'}
if __name__=='__main__':build(SOURCE,META,PALETTE,add_building)
