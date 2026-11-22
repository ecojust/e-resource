"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from rights import CREDIT, PHOTO, LICENSE, GEOMETRY, COPYRIGHT, write_metadata
from hall_braces import PALETTE,add_building
META={'id': 'huangpu-nanshi-power-station-hall-cross-bracing', 'name': '南市发电厂主厅右侧上下两层钢交叉撑', 'scope': '花园港路200号主厅的一个墙跨，两层深灰钢斜撑、连接两段的横向工字梁、两侧柱面和灰色分带。两层交点均可辨认；上部左端被梁遮住，模型在照片可见处截止。', 'model_scope_zh': '花园港路200号主厅的一个墙跨，两层深灰钢斜撑、连接两段的横向工字梁、两侧柱面和灰色分带。两层交点均可辨认；上部左端被梁遮住，模型在照片可见处截止。', 'estimated': '原照记录等效焦距24毫米。取两侧柱间约4米作为名义尺度，单照反投影给出两层净高合计约5.22米。开间、型钢厚度和杆件前后错位均待现场测量。', 'viewer_page': 'nanshi-power-station-hall-cross-bracing.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the visible braced bay, Y goes into the wall, and Z is up. All absolute dimensions are estimates.', 'interior_extent': 'One two-storey braced bay of the main hall'}
META.update(geometry_license=GEOMETRY, copyright=COPYRIGHT, photo_credit=CREDIT, photo_source=PHOTO,
            derivative_license_url=LICENSE)
if __name__=="__main__":
    write_metadata(package)
    package.build(SOURCE,META,PALETTE,add_building)
