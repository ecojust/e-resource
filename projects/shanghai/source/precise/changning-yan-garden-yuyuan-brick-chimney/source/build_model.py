"""Rebuild the photographed section of the red-brick chimney on Yuyuan Road."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools'for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from chimney import add_building,PALETTE
ID='changning-yan-garden-yuyuan-brick-chimney'
name='严家花园愚园路山墙红砖烟囱'
scope='据2018年2月13日愚园路699号街面照片，重建露出围墙的山墙红砖烟囱、两级收分台肩、灰色粗石墙与红瓦山檐。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='yan-garden-yuyuan-brick-chimney.html',reference_height_m=4.2,estimated='绝对尺寸和侧面进深按单幅街照砖模数估计，截取树枝间可辨的上段。',copyright='Original geometry and textures based on attributed references.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
