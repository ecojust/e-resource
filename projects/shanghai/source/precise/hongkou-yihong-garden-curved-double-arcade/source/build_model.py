"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from round_loggia import PALETTE,add_building
META={'id': 'hongkou-yihong-garden-curved-double-arcade', 'name': '扆虹园弧形端廊上下双券与铸铁栏杆', 'scope': '武进路扆虹园临园端廊，上下两层沿弯墙各开两道砖券。模型取两对通透的券孔、三道墩柱、上廊细铁栏和随弧线出挑的腰线与檐口。', 'model_scope_zh': '武进路扆虹园临园端廊，上下两层沿弯墙各开两道砖券。模型取两对通透的券孔、三道墩柱、上廊细铁栏和随弧线出挑的腰线与檐口。', 'estimated': '据2026年2月8日的公开实照测记当时修缮外观。单券净宽暂取1.63米，两层皆有透空；柱距、归圆半径、栏杆数量、檐与楼板进深属于比例估计。', 'viewer_page': 'yihong-garden-curved-double-arcade.html', 'source_reference_only': True, 'geometry_license': 'CC BY-SA 4.0', 'copyright': 'CC BY-SA 4.0. Windmemories，2026年2月8日摄，CC BY-SA 4.0。照片研究所涉的弧廊几何与渲染沿用同一许可。', 'photo_credit': 'Windmemories，2026年2月8日摄，CC BY-SA 4.0。照片研究所涉的弧廊几何与渲染沿用同一许可。', 'photo_source': 'https://commons.wikimedia.org/wiki/File:20260208_Ba_Jin_Library.jpg', 'derivative_license_url': 'https://creativecommons.org/licenses/by-sa/4.0'}
if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='CC BY-SA 4.0')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
