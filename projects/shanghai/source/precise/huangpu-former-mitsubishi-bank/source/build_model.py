"""Package the four-column south front of the former Mitsubishi Bank, 36 Jiujiang Road."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from bank_front import PALETTE,walls
ID='huangpu-former-mitsubishi-bank'
SCOPE='九江路36号2024年市住建委、市历保中心报道所见的花岗岩南立面、四根通高三层的巨柱、三段后退高窗、两端窗、门廊和台阶。保留原1993号源楼的后部及两侧独立邻屋。'
META={'id':ID,'name':'原三菱银行（九江路36号四柱门廊及南立面）','viewer_page':'former-mitsubishi-bank.html',
      'status':'original-photo-informed-exterior','scope':SCOPE,'model_scope_zh':SCOPE,'reference_height_m':22.93,
      'estimated':'街墙长约28.39米。柱头、檐口和墙身为照片比例估计，旗杆与两件铜狮按所见外形近似。','interiors_modeled':False,
      'source_register':'source/precise/'+ID+'/reference-review.json','coordinate_convention':'X follows Jiujiang Road west to east, Y enters the building, Z is height.',
      'copyright':'Original geometry and materials MIT. Photographs are linked as historical research. Sign typeface SIL OFL.'}
if __name__=='__main__':build(SOURCE,META,PALETTE,walls)
