"""Build and reopen the photographed rooftop pavilion of the Shanghai Commercial and Savings Bank."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from pavilion import PALETTE,add_building

ID='huangpu-shanghai-commercial-savings-bank-pavilion'
SCOPE='宁波路50号主楼南翼屋顶重檐歇山亭，街面可见的深红格扇、檐下梁头、绿釉瓦当、上翘角和局部镂空脊饰。两幅航片参照原南侧上檐估算占位。'
META={'id':ID,'name':'上海商业储蓄银行宁波路主楼重檐歇山楼亭','model_scope_zh':SCOPE,'scope':SCOPE,'estimated':'亭长宽、屋高、后侧封闭面和各构件断面为按照片比例的估计。','viewer_page':'shanghai-commercial-savings-bank-pavilion.html','status':'photo-informed-rooftop-detail','source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Metres. Z is up. Positive X follows the Ningbo Road cornice east. Negative Y faces the street. Z=0 is the existing roof support.','copyright':'Original model under MIT. Referenced photographs remain with their owners.'}

if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
