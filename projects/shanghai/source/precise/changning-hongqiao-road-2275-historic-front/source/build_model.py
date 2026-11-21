"""Rebuild the illustrated gable in the publisher's 2275 Hongqiao Road engraving."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from illustrated_gable import PALETTE,facade
ID='changning-hongqiao-road-2275-historic-front'
SCOPE='据学苑出版社《上海老洋房》署址钢笔画表现高山墙、窗格、两侧屋面与两根烟囱，模型止于图中可辨的上部轮廓。'
META={'id':ID,'name':'虹桥路2275号历史住宅山墙与屋顶','viewer_page':'hongqiao-road-2275-history.html','scope':SCOPE,'model_scope_zh':SCOPE,
      'reference_height_m':5.26,'estimated':'建筑年代未详，1994年入录，市房管局注约1996年灭失。线描出版于2015年、由学苑出版社于2020年重刊。模型截面比例取自线描，尺寸、灰调和进深均为估计。',
      'status':'historical-illustration-informed-facade-study','source_register':'source/precise/'+ID+'/reference-review.json',
      'coordinate_convention':'X runs across the drawing. Y is the depth of the modeled roof section. Z starts at the visible lower limit of the illustration.',
      'interiors_modeled':False,'copyright':'Original geometric interpretation of the described architectural features. No reference image pixels are embedded.'}
if __name__=='__main__':build(HERE,META,PALETTE,facade)
