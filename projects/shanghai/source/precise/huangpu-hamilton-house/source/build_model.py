"""Build the concave Hamilton House frontage and tower at 170 Middle Jiangxi Road."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from house import PALETTE,add_house

ID='huangpu-hamilton-house'
SCOPE=('江西中路170号汉弥登大楼东南街角主体的凹面五段、门廊三券、2017年可见“福州大楼”牌名、'
       '住宅窗带、空廊肩部、阶梯塔冠以及两端各一段短街墙。深处屋面、相连长翼、背面与室内另计。')
META=dict(id=ID,name='汉弥登大楼（江西中路170号街角、入口及塔冠）',viewer_page='hamilton-house.html',
          status='original-photo-and-footprint-informed-exterior',scope=SCOPE,model_scope_zh=SCOPE,
          estimated='由实名地块、2017年影像及针孔相机俯仰估算凹面曲率和约60.5米塔冠。退台进深、楼层和材质均为估计。',
          reference_height_m=60.53,interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',
          coordinate_convention='Author X southwest from Fuzhou to Jiangxi Road, Y southeast into the building, Z up.',
          copyright='Original architecture and materials MIT. Four raised sign characters use a renamed Noto Serif CJK SC subset, SIL OFL 1.1. No photograph is embedded.')
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_house)
