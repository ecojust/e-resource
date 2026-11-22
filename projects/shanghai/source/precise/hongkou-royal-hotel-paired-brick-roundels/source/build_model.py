"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from gable_rings import PALETTE,add_building
META={'id': 'hongkou-royal-hotel-paired-brick-roundels', 'name': '皇家旅馆旧址中段山墙的双圆窗与放射砖券', 'scope': '武进路393弄14号院内中段山墙的两圈圆窗砖券、伸出券面的四向压砖、三道壁柱与斜向压顶。', 'model_scope_zh': '武进路393弄14号院内中段山墙的两圈圆窗砖券、伸出券面的四向压砖、三道壁柱与斜向压顶。', 'estimated': '以2026年院内斜照测取砖环和壁柱。圆窗内径暂取0.79米，墙厚、砖长和砖数按比例估计。孔内深色部位的窗扇构造在照片中难辨。', 'viewer_page': 'royal-hotel-paired-brick-roundels.html', 'source_reference_only': True, 'geometry_license': 'CC BY-SA 4.0', 'copyright': 'Windmemories于2026年2月8日拍摄《20260208 Nong 393-14 Wujin Road.jpg》，CC BY-SA 4.0。依该照片重建的几何和模型渲染沿用同一许可。', 'photo_credit': 'Windmemories于2026年2月8日拍摄《20260208 Nong 393-14 Wujin Road.jpg》，CC BY-SA 4.0。依该照片重建的几何和模型渲染沿用同一许可。', 'photo_source': 'https://commons.wikimedia.org/wiki/File:20260208_Nong_393-14_Wujin_Road.jpg', 'derivative_license_url': 'https://creativecommons.org/licenses/by-sa/4.0'}
if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='CC BY-SA 4.0')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
