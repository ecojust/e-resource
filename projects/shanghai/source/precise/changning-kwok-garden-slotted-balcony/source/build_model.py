"""Build the photographed slotted balcony and the clipped gable at Lane 949."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools'for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from garden_balcony import add_building,PALETTE
ID='changning-kwok-garden-slotted-balcony'
name='郭氏花园住宅折坡山墙木阳台'
scope='取2014年刊出的同一屋面仰视及木栏近照，制作上层木阳台的透孔栏板、外露托梁和折坡山墙下的构架与双窗。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='kwok-garden-slotted-balcony.html',reference_height_m=2.79,estimated='进深、构架截面、栏板节距与色彩按照片近似。',copyright='Original geometry and generated materials based on attributed references.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
