"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from ornament_rights import CREDIT, PHOTO, LICENSE, GEOMETRY, COPYRIGHT, write_metadata
from brass_fan_gate import PALETTE,add_building
META={'id': 'huangpu-hongyu-textile-no443-brass-fan-gate', 'name': '鸿裕纺织有限公司大楼443号券门与镂空铜饰', 'scope': '江西中路443号的拱券内有扇形铁栏，左右门扇各有一枚镂空菱形铜饰。券心上方突出楔石，右侧墙上有绿色443号牌。', 'model_scope_zh': '江西中路443号的拱券内有扇形铁栏，左右门扇各有一枚镂空菱形铜饰。券心上方突出楔石，右侧墙上有绿色443号牌。', 'estimated': '依据Antigng在2015年拍摄的《鸿元大楼》原幅及2017、2021年的街面影像，按可见门框宽约2.20米估算券面与门扇的比例。铜饰孔洞从原照逐件勾取；门下半部、灯具和后来加装的设备均超出取样范围。', 'viewer_page': 'hongyu-textile-no443-brass-fan-gate.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
META.update(geometry_license=GEOMETRY, copyright=COPYRIGHT, photo_credit=CREDIT, photo_source=PHOTO,
            derivative_license_url=LICENSE)
if __name__=="__main__":
    write_metadata(package)
    package.build(SOURCE,META,PALETTE,add_building)
