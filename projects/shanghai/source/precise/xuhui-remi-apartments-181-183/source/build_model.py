"""Build and package the measured shared gable of nos. 181 and 183."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from housefront import PALETTE,add_housefront

ID='xuhui-remi-apartments-181-183'
SCOPE='永康路181、183号共用的临街双门山墙，包括筒瓦大券、两扇退入的小券门、绿色门牌、上下两层双窗、红砖线脚和突出屋面的墙墩。'
META=dict(id=ID,name='永康新村永康路181、183号双门山墙',viewer_page='remi-apartments-181-183.html',
          scope=SCOPE,model_scope_zh=SCOPE,status='documented-terraced-house-front',
          estimated='前凸房面跨两户。尺度综合冻结分户边界、2013年发表的现场照片和2020年三处公共街景估算。门窗深度、遮挡区与饰面颜色为近似值。',
          coordinate_convention='Local +X runs west along Yongkang Road, +Y is inward and Z is up. In glTF +Z faces the road and +Y is up.',
          interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',
          copyright='Original mesh and vector digits MIT. Photographs remain with their owners.')
if __name__=='__main__':build(SOURCE,META,PALETTE,add_housefront)
