"""Rebuild the photograph-based north elevation and northeast entrance at 175 South Suzhou Road."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from north_front import PALETTE,make_front

ID='huangpu-yee-tsoong-tobacco-northeast-front'
SCOPE='南苏州路175号颐中大楼的北面七道长券窗、东北抹角入口与虎丘路相邻窄跨。'
META=dict(id=ID,name='颐中大楼南苏州路北面与东北抹角',status='original-photo-informed-exterior',
          scope=SCOPE,model_scope_zh=SCOPE,viewer_page='yee-tsoong-tobacco.html',
          estimated='市历保中心资料记1920年建造。按2015年上传的实照及2026年发表的建筑照片复原窗列、街角、窗裙和外挑檐。各层高度、抹角及构件出挑以图像比例估计。',
          coordinate_convention='X runs west along South Suzhou Road, Y points into the block, and glTF +Y is up.',
          source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,
          copyright='Original MIT geometry. Reference images are not embedded.')
if __name__=='__main__':
    build(SOURCE,META,PALETTE,make_front)
