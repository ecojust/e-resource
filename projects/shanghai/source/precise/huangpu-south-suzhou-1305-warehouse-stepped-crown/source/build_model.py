"""Rebuild the riverfront crown and its editable native file."""
from pathlib import Path
import os,sys
from crown import PALETTE,model
SOURCE=Path(__file__).absolute().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
META={'id':'huangpu-south-suzhou-1305-warehouse-stepped-crown','name':'南苏州路1305号仓库山字形圆饰及水泥压花壁柱','viewer_page':'south-suzhou-1305-warehouse-stepped-crown.html','scope':'南苏州路1305–1307号仓库河岸面中部三跨上墙的山字形檐冠、1933浅浮雕、圆饰、灰水泥压花和上下错阶壁柱。下界在两侧箭形纹样之下。','model_scope_zh':'河岸面三跨上墙与檐冠局部','interiors_modeled':False,'status':'photographed-street-elevation-fragment','coordinate_convention':'X向面向大楼的右侧（约向西），Y向楼内，Z向上，Z0为本段实证裁切下边。','source_register':'source/precise/huangpu-south-suzhou-1305-warehouse-stepped-crown/reference-review.json','estimated':'四个2019街景机位测得外侧两壁柱轴间约9.23米，舍去单站时9.12–9.61米；内侧约3.50米，3.42–3.83米。构件出墙量、砖面后深和纹样小刻线用图上阴影估计。','geometry_license':'MIT','all_dimensions_estimated':True,'photos_embedded':False,'third_party_models_embedded':False}
if __name__=='__main__':
    from package_architectural_model import build
    build(SOURCE,META,PALETTE,model)
