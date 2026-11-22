"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from porch import PALETTE,add_building
META={'id': 'jingan-theatre-academy-yuxiu-stone-porch', 'name': '上海戏剧学院毓琇楼弧形门罩与夹墙石阶', 'scope': '毓琇楼入口有四级直跑石阶，两边带矮坡墙和方形前墩。两根砖墩托起中央浅弧、两端平直的门罩，白色拱腹下悬小灯。模型截到门框和左扇，下部四阶及两侧石墙保留进深。', 'model_scope_zh': '毓琇楼入口有四级直跑石阶，两边带矮坡墙和方形前墩。两根砖墩托起中央浅弧、两端平直的门罩，白色拱腹下悬小灯。模型截到门框和左扇，下部四阶及两侧石墙保留进深。', 'estimated': '依据两次入院实拍及校方导览。梯段名义净宽1.84米，据正面照片比例估算踏步高和门罩进深；原门上彩色玻璃的纹样未重绘。', 'viewer_page': 'theatre-academy-yuxiu-stone-porch.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
