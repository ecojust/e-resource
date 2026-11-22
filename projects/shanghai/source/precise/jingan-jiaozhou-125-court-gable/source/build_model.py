"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from court_gable import PALETTE,add_building
META={'id': 'jingan-jiaozhou-125-court-gable', 'name': '胶州路125弄住宅院侧小山墙、红瓦和六格木窗', 'scope': '胶州路125弄住宅的院墙正面以浅粉色抹灰小山墙收头，两侧是黑色铁门。模型取墙头往院内延伸的四皮红瓦，以及画面左侧一樘双扇六格红木窗。', 'model_scope_zh': '胶州路125弄住宅的院墙正面以浅粉色抹灰小山墙收头，两侧是黑色铁门。模型取墙头往院内延伸的四皮红瓦，以及画面左侧一樘双扇六格红木窗。', 'estimated': '依据2017年原照量取山尖、檐口、窗台与两道铁门的相对位置。山墙名义宽1.64米，瓦片搭接、灰缝和窗洞进深依据斜照估计。', 'viewer_page': 'jiaozhou-125-court-gable.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
