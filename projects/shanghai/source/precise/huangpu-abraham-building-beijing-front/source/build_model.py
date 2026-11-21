from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from beijing_front import PALETTE, facade
ID = 'huangpu-abraham-building-beijing-front'
SCOPE = '北京东路向圆明园路的西段老墙，从浅凸窗到斜切角，包括底层券列、券石、双圆窗、三组老虎窗及屋面前缘。老楼东段、院侧与南面另建商场保留。'
META = {'id':ID, 'name':'益丰洋行大楼北京东路西端券窗与切角', 'viewer_page':'abraham-building.html',
        'status':'original-photo-informed-exterior', 'scope':SCOPE,'model_scope_zh':SCOPE,
        'estimated':'依据2012年修缮重开报道及2014年1月27日西端街景，在实名历史条楼外墙拟合。层高、窗洞进深与展示色彩按照片估计。',
        'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
        'coordinate_convention':'X increases toward the western street corner. Y points into the finished facade. Z is upward in metres.',
        'copyright':'Original geometry and materials, MIT. No third-party photo pixels or mesh data are embedded.'}
if __name__=='__main__':build(HERE,META,PALETTE,facade)
