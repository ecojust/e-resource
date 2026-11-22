"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from roof_study import PALETTE,add_building
META={'id': 'jingan-881-garden-villa-dormer-flues', 'name': '延安中路881号花园住宅庭院侧老虎窗与成对双管烟囱', 'scope': '花园住宅面向庭院的斜屋面上有一樘白面老虎窗，前沿包红褐色山形封檐板。后方两方烟囱各有两支烟管和凸出的浅色带。', 'model_scope_zh': '花园住宅面向庭院的斜屋面上有一樘白面老虎窗，前沿包红褐色山形封檐板。后方两方烟囱各有两支烟管和凸出的浅色带。', 'estimated': '三个街景观察位置交会得到两烟囱中心间约4.39米，各相机平面射线的最大残差0.55米。以局部窗台作零标高，烟道孔深、瓦缝和被栏杆遮挡的窗下沿为近似。', 'viewer_page': '881-garden-villa-dormer-flues.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
