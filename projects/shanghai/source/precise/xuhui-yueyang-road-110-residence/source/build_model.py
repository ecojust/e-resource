"""Rebuild the photographically documented garden elevation at 110 Yueyang Road."""
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from garden_front import PALETTE,facade

ID='xuhui-yueyang-road-110-residence'
SCOPE='岳阳路110号1930年代花园住宅的花园立面。依据2020年刊载照片，复原凸出的二层长窗、下层方柱雨篷、红褐色台阶、左侧阳台及右侧退进的窗带，屋面止于三段可见瓦坡。'
META={'id':ID,'name':'岳阳路110号住宅花园立面','viewer_page':'yueyang-road-110.html','model_scope_zh':SCOPE,'scope':SCOPE,
      'reference_height_m':9.27,'estimated':'依据2020年衡复风貌区资料所刊照片、《1948年上海行号图》与花园一面可辨比例估算，原业主尚待契据证实。','status':'original-photo-informed-exterior',
      'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'X follows the garden elevation to the right, Y extends into the building and Z is vertical.',
      'copyright':'Original model, geometric ornament and materials. Source photographs are not distributed with the assets.'}
if __name__=='__main__':
    build(HERE,META,PALETTE,facade)
