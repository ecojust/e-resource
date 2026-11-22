"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from canted_bay import PALETTE,add_building
META={'id': 'jingan-xiudeli-41-canted-bay-awning', 'name': '修德里41号住宅四联木窗、斜角窗与波齿雨篷', 'scope': '院内住宅立面画面左侧一跨。四联红褐色木窗退入较厚的洞口，边上另有一扇随折墙转向的木窗；窗台及窗上石带随转角折回。正窗上方的一道浅雨篷保留波齿前缘和端支撑。', 'model_scope_zh': '院内住宅立面画面左侧一跨。四联红褐色木窗退入较厚的洞口，边上另有一扇随折墙转向的木窗；窗台及窗上石带随转角折回。正窗上方的一道浅雨篷保留波齿前缘和端支撑。', 'estimated': '按2019年照片校核正面四扇、侧面一扇和石带转折。正面墙段名义宽2.45米，侧墙长度约0.96米；雨篷材料、窗洞深度及斜角均为估计。外加管线、爬藤与窗外铁丝不纳入房屋构件。', 'viewer_page': 'xiudeli-41-canted-bay-awning.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
