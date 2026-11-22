"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from ornament_rights import CREDIT, PHOTO, LICENSE, GEOMETRY, COPYRIGHT, write_metadata
from garden_pediment import PALETTE,add_building
META={'id': 'jingan-jialu-garden-wall-floral-pediment', 'name': '佳庐庭墙尖顶石匾与卷叶花瓶浮雕', 'scope': '正面为庭墙临街石匾的尖顶卷叶雕饰。中央果盘或花瓶向上张开，左右叶茎成对回卷，尖顶两端折回短平檐，下部压有四道水平石线。', 'model_scope_zh': '正面为庭墙临街石匾的尖顶卷叶雕饰。中央果盘或花瓶向上张开，左右叶茎成对回卷，尖顶两端折回短平檐，下部压有四道水平石线。', 'estimated': '按2017年实照上的四角校正透视。取两侧短平檐之间约3.0米作为名义宽度。浮雕起伏约1至4厘米，实际刻深和背面均未测量。', 'viewer_page': 'jialu-garden-wall-floral-pediment.html', 'copyright': '浮雕轮廓、投影和色阶据Antigng于2017年8月9日拍摄的《北京西路1592弄11号》校正透视后制作。浅色雕饰的起伏是单张照片估算，照片及相应浮雕改编依CC BY-SA 4.0授权。'}
META.update(geometry_license=GEOMETRY, copyright=COPYRIGHT, photo_credit=CREDIT, photo_source=PHOTO, derivative_license_url=LICENSE)
if __name__=="__main__":
    write_metadata(package)
    package.build(SOURCE,META,PALETTE,add_building)
