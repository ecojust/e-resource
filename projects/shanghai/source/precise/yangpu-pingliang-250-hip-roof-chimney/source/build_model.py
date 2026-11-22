"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from chimney import PALETTE,add_building
META={'id': 'yangpu-pingliang-250-hip-roof-chimney', 'name': '平凉路250号住宅红砖烟囱与斜坡瓦面', 'scope': '平凉路后排屋顶的一座方形红砖烟囱。可从树间看到增厚的顶圈，其下有一层暗红悬挑砖；下方红瓦屋面斜向烟囱，右侧与另一坡面相接。', 'model_scope_zh': '平凉路后排屋顶的一座方形红砖烟囱。可从树间看到增厚的顶圈，其下有一层暗红悬挑砖；下方红瓦屋面斜向烟囱，右侧与另一坡面相接。', 'estimated': '2019年5月与2021年2月的街景分别从北面和西面量取。砖身正面取1.10米宽，露出瓦面的高度约2.1米。上口受树木遮挡，内孔、顶帽背面和瓦沟防水细部未获实测。', 'viewer_page': 'pingliang-250-hip-roof-chimney.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
