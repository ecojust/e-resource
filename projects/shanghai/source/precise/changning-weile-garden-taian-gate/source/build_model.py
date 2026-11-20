"""Rebuild the arched entrance and photographed walls of Willow Garden."""
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from gate import PALETTE,model

ID='changning-weile-garden-taian-gate'
SCOPE='泰安路120弄街门的拱券、双侧浮雕门墩、中央陶饰、筒瓦压顶、开启的铁门，以及两边能从2014和2021年照片相互辨识的院墙。1至31号住宅及远端院墙另列。'
META={'id':ID,'name':'卫乐园泰安路120弄街门','viewer_page':'weile-garden-gate.html','model_scope_zh':SCOPE,
      'scope':SCOPE,'reference_height_m':6.41,'estimated':'位置与拱脚净宽由两站街景方向交会估算，高宽比例来自2014年正立面摄影。',
      'source_register':'source/precise/'+ID+'/reference-review.json','status':'original-photo-informed-exterior',
      'interiors_modeled':False,'coordinate_convention':'X east-northeast along the exterior wall, Y north-northwest into the lane, Z up.',
      'copyright':'Original meshes and materials. No source photographs embedded.'}
if __name__=='__main__':
    build(HERE,META,PALETTE,model)
