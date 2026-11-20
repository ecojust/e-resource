"""Rebuild the courtyard elevation of Feng Zikai's Riyue Lou in Verdun Gardens."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from courtyard import PALETTE
from dwelling import model
ID='huangpu-feng-zikai-riyue-lou'
SCOPE='陕西南路39弄93号丰子恺旧居朝南的小庭院立面、双扇门、两侧窗、正对庭院的梯形二楼窗及局部尖顶。西面91号、东部住宅、后段、室内和另有独立门牌的38号保留另计。'
META={'id':ID,'name':'长乐邨93号丰子恺旧居（日月楼南庭院立面）','viewer_page':'feng-zikai-riyue-lou.html','model_scope_zh':SCOPE,'scope':SCOPE,'reference_height_m':8.068,'estimated':'单元横面和局部屋面据排屋轮廓、门牌点和实景比例推估；影像没有提供测绘图。','status':'original-photo-informed-exterior','source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'X east-northeast along the terrace, Y north-northwest from the courtyard into the house, Z up.','copyright':'Original geometry and materials. No photographs or private interiors are embedded.'}
if __name__=='__main__':build(HERE,META,PALETTE,model)
