"""Build the photographed fluted pilasters and carved spandrel of the high court."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent;roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
sys.path.insert(0,str(next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())))
from package_architectural_model import build
from court_bay import ID,PALETTE,add_building,texture
name='浙江北路高等法院旧址卷首壁柱与几何窗间墙'
scope='依据Fayhoo于2016年2月28日拍摄的浙江北路191号高等法院旧址照片，制作两根卷首壁柱、几何窗间墙与上下两组钢窗。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='special-district-high-court-fluted-spandrel.html',reference_height_m=6.70,estimated='构件宽深从单幅照片作相对估算，未测绘立面轴线。',copyright='Original mesh, UVs and generated materials.')
if __name__=='__main__':texture();build(source,META,PALETTE,add_building)
