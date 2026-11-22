"""Build the offset courtyard window bays pictured in the Shanghai dance-campus register."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent;roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
sys.path.insert(0,str(next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())))
from package_architectural_model import build
from court_bay import ID,PALETTE,add_building,texture
name='虹桥路舞蹈院团花园住宅群院内错台窗间与灰石基'
scope='依据区规资局虹桥路1674、1650号花园住宅群题照，提取院景中灰色块石状墙面、退入的中央窗间和相邻上层窗。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='dance-campus-recessed-court-bay.html',reference_height_m=4.78,estimated='相对宽深依据单幅照片估算。具体旧楼号及绝对位置待复核。',copyright='Original mesh, UVs and generated materials.')
if __name__=='__main__':texture();build(source,META,PALETTE,add_building)
