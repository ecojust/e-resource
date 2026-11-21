"""Rebuild the historically documented south elevation at 151 Yongfu Road."""
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from garden_front import PALETTE,model

ID='xuhui-yongfu-road-151-south-front'
SCOPE='永福路151号1941至1942年花园住宅的南向三开间，含西侧半圆螺旋柱窗廊、中央叠层栏杆及曲线女儿墙、东侧上下两排三连拱窗。两端止于照片可见的檐部。'
META={'id':ID,'name':'永福路151号花园住宅南立面','viewer_page':'yongfu-road-151.html','model_scope_zh':SCOPE,'scope':SCOPE,
      'reference_height_m':11.92,'estimated':'依2013年照片和市历史建筑保护事务中心资料图作比例复原，绝对尺寸非测绘值。','status':'original-photo-informed-exterior',
      'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'X east along the three bays, Y into the facade section, Z vertically upward.',
      'copyright':'Original model, geometric ornament and materials. Source photographs are not distributed with the assets.'}
if __name__=='__main__':
    build(HERE,META,PALETTE,model)
