"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from stone_vases import PALETTE,add_building
META={'id': 'hongkou-sanduoli-no53-paired-planter-lintel', 'name': '三多里53号石库门门楣双花盆、齿饰与挑檐', 'scope': '两盆带竖棱的石刻盆栽夹住一块低平的石匾。上面一排短齿托住挑出的檐线，中央另有带卷茎花饰的上匾。', 'model_scope_zh': '两盆带竖棱的石刻盆栽夹住一块低平的石匾。上面一排短齿托住挑出的檐线，中央另有带卷茎花饰的上匾。', 'estimated': '据高参88在2015年10月17日发表的成组照片绘制。正面门牌可读53，另两户只参照相同构造。总宽取2.63米为估值；匾上磨损笔画未补，盆栽叶片、卷茎和石刻凸出深度按可见轮廓估算。', 'viewer_page': 'sanduoli-no53-paired-planter-lintel.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
