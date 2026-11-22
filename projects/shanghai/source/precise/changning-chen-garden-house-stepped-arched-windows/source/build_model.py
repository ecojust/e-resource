"""Build the three stair-stepped round-headed windows of the Chen family garden residence."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from stair_windows import ID,PALETTE,add_building
name='陈氏花园住宅阶梯三拱窗与绞绳柱'
scope='按虹桥街道展览所供陈氏花园住宅实照，建虹桥路1440号墙上三级上升的半圆拱窗、扇光窗和两根绞绳柱。'
META=dict(id=ID,name=name,scope=scope,model_scope_zh=scope,viewer_page='chen-garden-stepped-arch-windows.html',reference_height_m=3.998,estimated='窗高宽、落差、绞绳柱与窗框关系取自实照；绝对尺度、玻璃厚度和螺旋背部为近似。',copyright='Original mesh, UVs and procedural roughcast.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
