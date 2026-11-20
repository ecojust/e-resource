"""Build the bank and apartment frontage on the distinct Yates Apartments parcel."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from yates_geometry import PALETTE,make_yates
from final_preview import finish
ID='jingan-yates-apartments'
SCOPE='静安区南京西路801–803号同孚大楼。以半月形楼体、八排连续公寓窗、银行与住宅入口、北端楼梯塔和吴江路端圆柱体现已核外观。两排楼顶露台柱及背面服务廊参照街区专著的记述作比例估计。'
META={'id':ID,'name':'同孚大楼（中国银行西区分行旧址）','status':'original-photo-informed-exterior','scope':SCOPE,'model_scope_zh':SCOPE,'viewer_page':'yates-apartments.html',
      'estimated':'街曲线按具名独立源、三个航片版本和照片推定。区志记高34.45米，本模型将其作为塔顶控制值。窗间距、露台和隐蔽后墙为估计。',
      'coordinate_convention':'glTF +Y up, +Z outward to the convex northeast street front, +X northwest toward the Nanjing Road residential entrance.',
      'source_register':f'source/precise/{ID}/reference-review.json','interiors_modeled':False,
      'copyright':'Original geometric reconstruction MIT. Renamed entrance lettering subset SIL OFL 1.1. Source photographs referenced separately.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,make_yates)
    finish()
