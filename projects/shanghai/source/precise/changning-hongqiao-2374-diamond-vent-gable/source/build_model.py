"""Build the photographed diamond-vent gable and Roman-tile roof at 2374 Hongqiao Road."""
from pathlib import Path
import os,sys
src=Path(__file__).resolve().parent
roots=list(src.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from gable import ID,PALETTE,add_building,texture
title='虹桥路2374号花园住宅菱孔山墙与筒瓦'
scope='长宁区规划资源局题照中，右前小山墙的菱孔、搭接筒瓦、檐口及下部张开的钢窗。'
META=dict(id=ID,name=title,scope=scope,model_scope_zh=scope,viewer_page='hongqiao-2374-diamond-vent-gable.html',reference_height_m=3.14,estimated='依照片比例估算各构件，侧截边在照片可见范围内。',copyright='Original geometry, UVs and tile textures.')
if __name__=='__main__':texture();build(src,META,PALETTE,add_building)
