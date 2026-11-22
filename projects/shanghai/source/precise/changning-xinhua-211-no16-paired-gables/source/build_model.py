"""Build the unequal dormer and gable windows at 16, Lane 211 Xinhua Road."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from street_dormers import ID,PALETTE,add_building
name='新华路211弄16号花园住宅老虎窗与相邻山墙'
scope='按2016年1月15日有门牌近照的成组实拍制作侧面屋坡、较窄老虎窗、向前挑出的大山墙及遮雨窗罩。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='xinhua-211-no16-paired-gables.html',reference_height_m=2.83,estimated='露出的体量关系、板带与开窗据现场照片。绝对尺寸、断面及隐藏接缝为推定。',copyright='Original mesh, UVs and procedural tile surface.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
